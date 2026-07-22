"""
train_with_mlflow.py
---------------------
Same training logic as train.py, wrapped with MLflow tracking + registry.
Why a separate wrapper instead of editing train.py: keeps the core modeling
code importable/testable without an MLflow server dependency; this file is
the "production" entrypoint that adds the tracking layer around it.
"""
import mlflow
import mlflow.xgboost
import pandas as pd
import numpy as np
import xgboost as xgb

from config import FEATURE_TABLE_PATH, HORIZONS, RANDOM_SEED
from features import FEATURE_COLUMNS
from train import get_xy, tune_horizon, seasonal_naive_baseline, mape

mlflow.set_tracking_uri("http://mlflow-server:5000")  # swap for your MLflow server
mlflow.set_experiment("oon_cost_forecasting")


def train_and_log_all_horizons(n_trials: int = 25):
    df = pd.read_csv(FEATURE_TABLE_PATH, parse_dates=["month"])
    df["region"] = df["region"].astype("category")
    df["specialty"] = df["specialty"].astype("category")

    for h in HORIZONS:
        with mlflow.start_run(run_name=f"xgb_h{h}"):
            X, y, valid = get_xy(df, h)
            cutoff = valid["month"].quantile(0.8)
            train_mask = valid["month"] <= cutoff
            X_train, y_train = X[train_mask], y[train_mask]
            X_test, y_test = X[~train_mask], y[~train_mask]

            baseline_mape = seasonal_naive_baseline(df, h)
            best_params = tune_horizon(X_train, y_train, n_trials=n_trials)

            model = xgb.XGBRegressor(**best_params, objective="reg:squarederror",
                                      enable_categorical=True, random_state=RANDOM_SEED)
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            y_true, y_pred = np.expm1(y_test), np.expm1(pred)
            xgb_mape = mape(y_true, y_pred)

            # log everything needed to reproduce & compare runs later:
            # params, metrics, and the model artifact itself.
            mlflow.log_params(best_params)
            mlflow.log_param("horizon", h)
            mlflow.log_metric("baseline_mape", baseline_mape)
            mlflow.log_metric("xgb_mape", xgb_mape)
            mlflow.log_metric("n_train", len(X_train))
            mlflow.log_metric("n_test", len(X_test))

            # registers the model as a new (unstaged) version; the DAG's
            # promote_if_better task decides whether it becomes Production
            mlflow.xgboost.log_model(model, artifact_path="model",
                                      registered_model_name=f"oon_xgb_h{h}")

            print(f"h={h}: logged run, xgb_mape={xgb_mape:.2f} vs baseline={baseline_mape:.2f}")


if __name__ == "__main__":
    train_and_log_all_horizons()
