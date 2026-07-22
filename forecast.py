"""
forecast.py
-----------
Uses the latest row of history per (region, specialty) to generate 1-6 month
forecasts with 80% prediction intervals, then applies alert logic the
network team consumes directly.
"""
import numpy as np
import pandas as pd
import xgboost as xgb

from config import (FEATURE_TABLE_PATH, HORIZONS, MODEL_PATH_TEMPLATE,
                     QUANTILE_MODEL_TEMPLATE, FORECAST_OUTPUT_PATH,
                     ALERT_HIGH_THRESHOLD, ALERT_WATCH_THRESHOLD)
from features import FEATURE_COLUMNS


def load_model(h):
    m = xgb.XGBRegressor()
    m.load_model(MODEL_PATH_TEMPLATE.format(h=h))
    return m


def load_quantile_model(h, q):
    m = xgb.XGBRegressor()
    m.load_model(QUANTILE_MODEL_TEMPLATE.format(h=h, q=str(q).replace(".", "")))
    return m


def alert_label(current, forecast_6m, lower_6m):
    """
    Alert only fires HIGH if BOTH the point forecast AND the lower bound of
    the interval are rising -- this is what keeps precision high (design
    doc's ">70% precision, avoid crying wolf" requirement). A point forecast
    alone can be rising just from noise; requiring the lower bound to also
    rise means we're confident even in the pessimistic scenario.
    """
    growth = (forecast_6m - current) / (abs(current) + 1e-6)
    lower_growth = (lower_6m - current) / (abs(current) + 1e-6)
    if growth > ALERT_HIGH_THRESHOLD and lower_growth > 0:
        return "HIGH", growth
    elif growth > ALERT_WATCH_THRESHOLD:
        return "WATCH", growth
    return "OK", growth


def generate_forecasts():
    df = pd.read_csv(FEATURE_TABLE_PATH, parse_dates=["month"])
    df["region"] = df["region"].astype("category")
    df["specialty"] = df["specialty"].astype("category")

    latest = df.sort_values("month").groupby(["region", "specialty"]).tail(1).copy()
    X_latest = latest[FEATURE_COLUMNS]

    results = {"region": latest["region"].values, "specialty": latest["specialty"].values,
               "current_cost": np.expm1(latest["y"]).values}

    for h in HORIZONS:
        model = load_model(h)
        pred_log = model.predict(X_latest)
        results[f"forecast_h{h}"] = np.expm1(pred_log)
        if h == 6:
            lo_model, hi_model = load_quantile_model(h, 0.1), load_quantile_model(h, 0.9)
            results["lower_80_h6"] = np.expm1(lo_model.predict(X_latest))
            results["upper_80_h6"] = np.expm1(hi_model.predict(X_latest))

    out = pd.DataFrame(results)
    labels, growths = [], []
    for _, row in out.iterrows():
        label, growth = alert_label(row["current_cost"], row["forecast_h6"], row["lower_80_h6"])
        labels.append(label)
        growths.append(growth)
    out["alert"] = labels
    out["growth_6m_pct"] = np.array(growths) * 100

    out = out.sort_values("growth_6m_pct", ascending=False).reset_index(drop=True)
    out.to_csv(FORECAST_OUTPUT_PATH, index=False)
    print(f"forecast table ({len(out)} segments) -> {FORECAST_OUTPUT_PATH}")
    print(out[["region", "specialty", "current_cost", "forecast_h1", "forecast_h6",
               "growth_6m_pct", "alert"]].head(10).to_string(index=False))
    return out


if __name__ == "__main__":
    generate_forecasts()
