"""
features.py
-----------
Reframes forecasting as supervised regression: for every (region, specialty,
month) row, build features from strictly *past* information, and a target
that is the *future* oon_cost at each horizon h in HORIZONS (direct
multi-horizon forecasting -- one target column per horizon, rather than
feeding predictions back in recursively, which compounds error).
"""
import numpy as np
import pandas as pd
from config import MODELING_TABLE_PATH, FEATURE_TABLE_PATH, LAGS, ROLLING_WINDOWS, HORIZONS


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["region", "specialty", "month"]).copy()
    g = df.groupby(["region", "specialty"])["y"]
    for lag in LAGS:
        # Lags chosen from ACF/PACF: 1-3 = short momentum, 6/12 = half-year
        # and yearly seasonality signal.
        df[f"lag_{lag}"] = g.shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    CRITICAL leakage guard: always .shift(1) *before* the rolling window.
    Without the shift, a rolling mean at month t would include y_t itself --
    the model would partly be "predicting" using the answer.
    """
    df = df.sort_values(["region", "specialty", "month"]).copy()
    shifted = df.groupby(["region", "specialty"])["y"].shift(1)
    for w in ROLLING_WINDOWS:
        df[f"roll_mean_{w}"] = shifted.groupby([df["region"], df["specialty"]]).transform(
            lambda s: s.rolling(w, min_periods=max(2, w // 2)).mean()
        )
        df[f"roll_std_{w}"] = shifted.groupby([df["region"], df["specialty"]]).transform(
            lambda s: s.rolling(w, min_periods=max(2, w // 2)).std()
        )
    return df


def add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trees can't extrapolate a trend past values they've seen. Momentum
    features (rate of change, acceleration) let the model recognize "this
    segment is accelerating" even without ever seeing the future value --
    it maps momentum patterns it HAS seen elsewhere to a higher predicted
    level here.
    """
    df["mom_change_1_3"] = df["lag_1"] - df["lag_3"]
    df["trend_ratio_3_12"] = (df["roll_mean_3"] - df["roll_mean_12"]) / (df["roll_mean_12"].abs() + 1e-6)
    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df["month_num"] = df["month"].dt.month
    df["quarter"] = df["month"].dt.quarter
    # cyclical encoding so December and January are numerically adjacent
    df["month_sin"] = np.sin(2 * np.pi * df["month_num"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month_num"] / 12)
    return df


def add_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    These are the features that make the model's story causal, not just
    statistical: fewer in-network providers + longer waits explain WHY OON
    cost rises, which is what earns the network team's trust in SHAP plots.
    """
    df["provider_density_delta"] = df.groupby(["region", "specialty"])["in_network_providers"].diff()
    df["wait_days_delta"] = df.groupby(["region", "specialty"])["avg_appointment_wait_days"].diff()
    return df


def add_direct_horizon_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Direct (not recursive) multi-step forecasting: build one target column
    per horizon by shifting y *backwards* (i.e., pulling a future value onto
    the current row). Training a separate model per horizon avoids
    compounding one-step errors forward, at the cost of training H models
    instead of one -- cheap at monthly grain.
    """
    df = df.sort_values(["region", "specialty", "month"]).copy()
    for h in HORIZONS:
        df[f"target_h{h}"] = df.groupby(["region", "specialty"])["y"].shift(-h)
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Region/specialty are categorical with a business-explainable identity;
    we keep them as XGBoost native categorical dtype instead of one-hot
    (fewer columns, and XGBoost's histogram splits handle it natively),
    which also plays nicer with the tree's handling of unseen categories.
    """
    df["region"] = df["region"].astype("category")
    df["specialty"] = df["specialty"].astype("category")
    return df


def build_feature_table() -> pd.DataFrame:
    df = pd.read_csv(MODELING_TABLE_PATH, parse_dates=["month"])
    df = add_lag_features(df)
    df = add_rolling_features(df)
    df = add_momentum_features(df)
    df = add_calendar_features(df)
    df = add_domain_features(df)
    df = add_direct_horizon_targets(df)
    df = encode_categoricals(df)
    df.to_csv(FEATURE_TABLE_PATH, index=False)
    print(f"feature table: {df.shape} -> {FEATURE_TABLE_PATH}")
    return df


FEATURE_COLUMNS = (
    [f"lag_{l}" for l in LAGS]
    + [f"roll_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"roll_std_{w}" for w in ROLLING_WINDOWS]
    + ["mom_change_1_3", "trend_ratio_3_12", "month_num", "quarter", "month_sin", "month_cos",
       "in_network_providers", "avg_appointment_wait_days", "terminations_last_month",
       "provider_density_delta", "wait_days_delta", "oon_rate", "region", "specialty"]
)

if __name__ == "__main__":
    build_feature_table()
