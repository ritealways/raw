"""
train.py
--------
1. Baselines (Seasonal Naive) -- any "smart" model must beat this or it's not
   worth the complexity/maintenance cost.
2. Walk-forward CV (TimeSeriesSplit) + Optuna tuning of one XGBoost model per
   horizon.
3. Quantile (pinball-loss) models at q=0.1/0.9 for prediction intervals.

Why walk-forward, not random K-fold: random shuffling would let the model
train on "future" months and validate on "past" months relative to it --
the single most common time-series leakage bug.
"""
import json
import numpy as np
import pandas as pd
import optuna
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

from config import (FEATURE_TABLE_PATH, HORIZONS, RANDOM_SEED, MODEL_PATH_TEMPLATE,
                     QUANTILE_MODEL_TEMPLATE, METRICS_PATH)
from features import FEATURE_COLUMNS

optuna.logging.set_verbosity(optuna.logging.WARNING)


def mape(y_true, y_pred, eps=1e-6):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + eps))) * 100)


def seasonal_naive_baseline(df: pd.DataFrame, h: int) -> float:
    """Predict oon_cost(t+h) with oon_cost(t+h-12) (last year, same month) if
    available, else oon_cost(t). Any real model must clear this bar."""
    df = df.dropna(subset=[f"target_h{h}"]).copy()
    df["naive_pred"] = df.groupby(["region", "specialty"])["y"].shift(12 - h)
    df["naive_pred"] = df["naive_pred"].fillna(df["y"])
    valid = df.dropna(subset=["naive_pred"])
    return mape(np.expm1(valid[f"target_h{h}"]), np.expm1(valid["naive_pred"]))


def get_xy(df: pd.DataFrame, h: int):
    target_col = f"target_h{h}"
    valid = df.dropna(subset=[target_col] + FEATURE_COLUMNS[:len(FEATURE_COLUMNS) - 2])
    X = valid[FEATURE_COLUMNS]
    y = valid[target_col]
    return X, y, valid


def tune_horizon(X: pd.DataFrame, y: pd.Series, n_trials: int = 20) -> dict:
    """
    Optuna search over the params that matter most for short, noisy monthly
    series: shallow max_depth to avoid overfitting a 40-60 point history,
    low learning_rate + more trees for stability, subsample/colsample for
    regularization.
    """
    tscv = TimeSeriesSplit(n_splits=4)

    def objective(trial):
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 200, 800),
            max_depth=trial.suggest_int("max_depth", 3, 7),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 10),
            reg_lambda=trial.suggest_float("reg_lambda", 1, 10),
        )
        scores = []
        for tr_idx, va_idx in tscv.split(X):
            m = xgb.XGBRegressor(**params, objective="reg:squarederror",
                                  enable_categorical=True, random_state=RANDOM_SEED)
            m.fit(X.iloc[tr_idx], y.iloc[tr_idx])
            pred = m.predict(X.iloc[va_idx])
            scores.append(mape(np.expm1(y.iloc[va_idx]), np.expm1(pred)))
        return float(np.mean(scores))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params


def train_quantile_models(X: pd.DataFrame, y: pd.Series, best_params: dict, h: int):
    """Pinball-loss models at q=0.1/0.9 give an 80% prediction interval, so
    the network team can act only on high-confidence rising alerts."""
    for q in [0.1, 0.9]:
        m = xgb.XGBRegressor(**best_params, objective="reg:quantileerror", quantile_alpha=q,
                              enable_categorical=True, random_state=RANDOM_SEED)
        m.fit(X, y)
        m.save_model(QUANTILE_MODEL_TEMPLATE.format(h=h, q=str(q).replace(".", "")))


def train_all_horizons(n_trials: int = 15):
    df = pd.read_csv(FEATURE_TABLE_PATH, parse_dates=["month"])
    df["region"] = df["region"].astype("category")
    df["specialty"] = df["specialty"].astype("category")

    metrics = {}
    for h in HORIZONS:
        X, y, valid = get_xy(df, h)

        # last 20% of *time*, not random rows, held out as the true test set
        cutoff = valid["month"].quantile(0.8)
        train_mask = valid["month"] <= cutoff
        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[~train_mask], y[~train_mask]

        baseline_mape = seasonal_naive_baseline(df, h)

        best_params = tune_horizon(X_train, y_train, n_trials=n_trials)
        final_model = xgb.XGBRegressor(**best_params, objective="reg:squarederror",
                                        enable_categorical=True, random_state=RANDOM_SEED)
        final_model.fit(X_train, y_train)
        pred = final_model.predict(X_test)

        y_true_dollars = np.expm1(y_test)
        y_pred_dollars = np.expm1(pred)
        m = mape(y_true_dollars, y_pred_dollars)
        rmse = float(np.sqrt(np.mean((y_true_dollars - y_pred_dollars) ** 2)))
        mae = float(np.mean(np.abs(y_true_dollars - y_pred_dollars)))
        wape = float(np.sum(np.abs(y_true_dollars - y_pred_dollars)) / np.sum(np.abs(y_true_dollars)) * 100)
        direction_true = np.sign(y_true_dollars.values - np.expm1(X_test["lag_1"]))
        direction_pred = np.sign(y_pred_dollars - np.expm1(X_test["lag_1"]))
        direction_acc = float(np.mean(direction_true == direction_pred) * 100)

        metrics[f"h{h}"] = {
            "baseline_seasonal_naive_mape": baseline_mape,
            "xgb_mape": m, "xgb_rmse": rmse, "xgb_mae": mae, "xgb_wape": wape,
            "direction_accuracy_pct": direction_acc, "best_params": best_params,
            "n_train": int(len(X_train)), "n_test": int(len(X_test)),
        }
        print(f"h={h}: baseline MAPE={baseline_mape:.1f}%  xgb MAPE={m:.1f}%  "
              f"WAPE={wape:.1f}%  dir_acc={direction_acc:.1f}%")

        final_model.save_model(MODEL_PATH_TEMPLATE.format(h=h))
        # refit quantile models on the full train split for interval forecasts
        train_quantile_models(X_train, y_train, best_params, h)

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"metrics -> {METRICS_PATH}")
    return metrics


if __name__ == "__main__":
    train_all_horizons(n_trials=15)
