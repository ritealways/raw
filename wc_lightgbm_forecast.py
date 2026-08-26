"""
wc_lightgbm_forecast.py
------------------------------------------------------------
END-TO-END FORECASTING SCRIPT

What this script does, in plain English, step by step:

    STEP 1  Log in to the mock Anaplan server (get a Bearer token)
    STEP 2  Pull ("export") the historical input data from Anaplan
    STEP 3  Train 3 LightGBM models (a "quantile regression" approach)
            to predict Avg_Wage at the 10th, 50th (median) and 90th
            percentile - this gives you a low / typical / high forecast
    STEP 4  Build future rows (next N months) for each Region / Channel /
            Industry_Class / Account_Size combination found in the data
    STEP 5  Predict P10 / P50 / P90 for those future rows
    STEP 6  Push ("import") the forecast results back into the mock
            Anaplan server as a CSV file
    STEP 7  Verify the round trip by downloading the file back out

Run it with:
    python wc_lightgbm_forecast.py

Requires the mock server (mock_anaplan_server.py) to already be running
on http://127.0.0.1:8000
------------------------------------------------------------
"""

import io
import time
import sys

import pandas as pd
import numpy as np
import requests
from lightgbm import LGBMRegressor

# ------------------------------------------------------------
# CONFIG - change these if your mock server runs somewhere else
# ------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"
WORKSPACE_ID = "wrk-001"
MODEL_ID = "mod-101"
INPUT_FILE_ID = "file-201"
OUTPUT_FILE_ID = "file-202"
IMPORT_PROCESS_ID = "proc-301"

FORECAST_MONTHS = 3          # how many months ahead to forecast
TARGET_COLUMN = "Avg_Wage"   # what we are forecasting
CATEGORICAL_COLS = ["Region", "Channel", "Industry_Class", "Account_Size"]


def log(msg: str):
    print(f"[wc_lightgbm] {msg}")


# ============================================================
# STEP 1: LOGIN
# ============================================================
def login() -> str:
    log("STEP 1: Logging in to mock Anaplan server...")
    resp = requests.post(f"{BASE_URL}/oauth2/token", data={
        "grant_type": "client_credentials",
        "client_id": "demo-client",
        "client_secret": "demo-secret",
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    log(f"  -> Got token: {token[:24]}...")
    return token


# ============================================================
# STEP 2: PULL INPUT DATA
# ============================================================
def fetch_input_data(token: str) -> pd.DataFrame:
    log("STEP 2: Pulling historical input data from Anaplan (export)...")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{INPUT_FILE_ID}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df["Month"] = pd.to_datetime(df["Month"])
    log(f"  -> Received {len(df)} rows, {df['Month'].nunique()} months, "
        f"{df[CATEGORICAL_COLS].drop_duplicates().shape[0]} unique segments.")
    return df


# ============================================================
# FEATURE ENGINEERING HELPERS
# ============================================================
NUMERIC_FEATURE_COLS = [
    "Payroll", "Employee_Count", "Payroll_Growth_Rate_YoY", "Payroll_Growth_Rate_QoQ",
    "Hazard_Group", "Historical_Loss_Ratio", "Claim_Frequency", "Claim_Severity",
    "Wage_Inflation_Index", "Employer_Tenure", "Retention_Rate", "Churn_Probability",
    "Seasonality_Index", "Economic_Indicator", "Employment_Growth_Rate",
]


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month_index"] = (df["Month"].dt.year - df["Month"].dt.year.min()) * 12 + df["Month"].dt.month
    df["calendar_month"] = df["Month"].dt.month
    return df


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = add_time_features(df)
    for c in CATEGORICAL_COLS:
        df[c] = df[c].astype("category")
    return df


FEATURE_COLS = CATEGORICAL_COLS + NUMERIC_FEATURE_COLS + ["month_index", "calendar_month"]


# ============================================================
# STEP 3: TRAIN QUANTILE MODELS
# ============================================================
def train_quantile_models(df: pd.DataFrame) -> dict:
    log("STEP 3: Training LightGBM quantile models (P10 / P50 / P90)...")
    df = prepare_features(df)
    X = df[FEATURE_COLS]
    y = df[TARGET_COLUMN]

    models = {}
    for alpha, label in [(0.10, "P10"), (0.50, "P50"), (0.90, "P90")]:
        model = LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            num_leaves=15,
            min_child_samples=5,
            verbosity=-1,
        )
        model.fit(X, y, categorical_feature=CATEGORICAL_COLS)
        models[label] = model
        log(f"  -> Trained {label} model (quantile alpha={alpha})")
    return models


# ============================================================
# STEP 4: BUILD FUTURE ROWS TO FORECAST
# ============================================================
def build_future_rows(df: pd.DataFrame, months_ahead: int) -> pd.DataFrame:
    log(f"STEP 4: Building the next {months_ahead} month(s) of future rows per segment...")
    df_prepared = add_time_features(df)
    last_month = df["Month"].max()

    future_rows = []
    for keys, seg in df.groupby(CATEGORICAL_COLS, observed=True):
        seg = seg.sort_values("Month")
        latest = seg.iloc[-1]  # carry forward the most recent known feature values

        for step in range(1, months_ahead + 1):
            future_month = (last_month + pd.DateOffset(months=step)).replace(day=1)
            row = {c: v for c, v in zip(CATEGORICAL_COLS, keys)}
            row["Month"] = future_month
            for col in NUMERIC_FEATURE_COLS:
                row[col] = latest[col]  # simple carry-forward assumption
            future_rows.append(row)

    future_df = pd.DataFrame(future_rows)
    future_df = add_time_features(future_df)
    for c in CATEGORICAL_COLS:
        future_df[c] = future_df[c].astype("category")
    log(f"  -> Built {len(future_df)} future rows to forecast.")
    return future_df


# ============================================================
# STEP 5: PREDICT
# ============================================================
def predict(models: dict, future_df: pd.DataFrame) -> pd.DataFrame:
    log("STEP 5: Predicting P10 / P50 / P90 for future rows...")
    X_future = future_df[FEATURE_COLS]

    result = future_df[CATEGORICAL_COLS + ["Month"]].copy()
    for label, model in models.items():
        result[label] = model.predict(X_future).round(0)

    # enforce logical ordering P10 <= P50 <= P90 per row (quantile crossing safeguard)
    result[["P10", "P50", "P90"]] = np.sort(result[["P10", "P50", "P90"]].values, axis=1)
    result = result.rename(columns={"P50": "P50_Median"})
    log("  -> Forecast complete.")
    return result


# ============================================================
# STEP 6: PUSH RESULTS BACK TO ANAPLAN
# ============================================================
def push_forecast_to_anaplan(token: str, forecast_df: pd.DataFrame):
    log("STEP 6: Pushing forecast output back to Anaplan (import)...")
    headers = {"Authorization": f"Bearer {token}"}
    csv_text = forecast_df.to_csv(index=False)

    # 6a. Upload the CSV as chunk "0"
    upload_url = (f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}"
                  f"/files/{OUTPUT_FILE_ID}/chunks/0")
    resp = requests.put(upload_url, headers=headers, data=csv_text.encode("utf-8"))
    resp.raise_for_status()
    log("  -> Chunk uploaded.")

    # 6b. Trigger the import process
    process_url = (f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}"
                    f"/processes/{IMPORT_PROCESS_ID}/tasks")
    resp = requests.post(process_url, headers=headers)
    resp.raise_for_status()
    task_id = resp.json()["taskId"]
    log(f"  -> Import process started, taskId={task_id}")

    # 6c. Poll task status until COMPLETE (in this mock it's instant, but we poll anyway
    #     the way you would against the real Anaplan API)
    status_url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/tasks/{task_id}"
    for _ in range(10):
        resp = requests.get(status_url, headers=headers)
        resp.raise_for_status()
        status = resp.json()["status"]
        if status == "COMPLETE":
            log("  -> Import task COMPLETE.")
            break
        time.sleep(0.5)
    else:
        log("  -> WARNING: task did not complete in time.")


# ============================================================
# STEP 7: VERIFY ROUND TRIP
# ============================================================
def verify_round_trip(token: str):
    log("STEP 7: Verifying by downloading the forecast output back from Anaplan...")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{OUTPUT_FILE_ID}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    log(f"  -> Confirmed: {len(df)} forecast rows are now stored in Anaplan.")
    return df


# ============================================================
# MAIN
# ============================================================
def main():
    try:
        token = login()
    except requests.exceptions.ConnectionError:
        log("ERROR: Could not connect to the mock Anaplan server.")
        log(f"       Make sure it's running at {BASE_URL} (see README for instructions).")
        sys.exit(1)

    history_df = fetch_input_data(token)
    models = train_quantile_models(history_df)
    future_df = build_future_rows(history_df, FORECAST_MONTHS)
    forecast_df = predict(models, future_df)

    print("\n--- FORECAST PREVIEW (long format, ready to push) ---")
    print(forecast_df.to_string(index=False))

    push_forecast_to_anaplan(token, forecast_df)
    final_df = verify_round_trip(token)

    print("\n--- CONFIRMED DATA NOW STORED IN MOCK ANAPLAN ---")
    print(final_df.to_string(index=False))

    # Also show one segment pivoted the way the screenshot displays it
    # (Region/Channel/Industry/Account Size fixed, Months across columns, P10/P50/P90 as rows)
    first_seg = final_df[CATEGORICAL_COLS].drop_duplicates().iloc[0]
    mask = (final_df[CATEGORICAL_COLS] == first_seg).all(axis=1)
    seg_df = final_df[mask].sort_values("Month")
    pivoted = seg_df.set_index("Month")[["P10", "P50_Median", "P90"]].T
    print(f"\n--- EXAMPLE PIVOTED VIEW (like the screenshot) for segment: "
          f"{first_seg.to_dict()} ---")
    print(pivoted.to_string())

    log("Done. Forecast successfully pulled, generated, and pushed to mock Anaplan.")


if __name__ == "__main__":
    main()
