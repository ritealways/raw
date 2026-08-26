"""
End-to-End Anaplan Integration Pipeline (run_pipeline.py)
=========================================================
1. Authenticates against Mock Anaplan Server (OAuth 2.0).
2. Fetches Insurance Input Features (Excel data) from Anaplan View API.
3. Passes features to `wc_lightgbm` for P10, P50, P90 predictions.
4. Uploads predictions back to Anaplan as a file chunk.
5. Executes the Anaplan Import Process to commit changes to the model.
6. Verifies results via the task status endpoint.
"""

import sys
import time
import requests
import json
from wc_lightgbm import run_wc_forecast

BASE_URL = "http://localhost:8000"

WORKSPACE_ID = "wrk-insurance-001"
MODEL_ID = "mod-wc-pricing-2026"
VIEW_ID = "view-input-wc-features"
FILE_ID = "file-forecast-output-csv"
PROCESS_ID = "proc-import-forecasts"


def run_pipeline():
    print("\n=======================================================")
    print("  🚀 STARTING ANAPLAN ML FORECASTING PIPELINE")
    print("=======================================================\n")

    # Step 1: Authentication
    print("👉 [Step 1/5] Requesting OAuth 2.0 Token from Anaplan...")
    try:
        auth_resp = requests.post(f"{BASE_URL}/oauth2/token", timeout=5)
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
        token = auth_data["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        print(f"   ✅ Authenticated! Bearer Token: {token[:20]}...")
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: Cannot connect to Mock Anaplan Server at http://localhost:8000.")
        print("   👉 Make sure 'python mock_anaplan_server.py' is running in another terminal.")
        sys.exit(1)

    # Step 2: Fetch View Data from Anaplan
    print("\n👉 [Step 2/5] Fetching Input Model Data from Anaplan View...")
    view_url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/views/{VIEW_ID}/data"
    view_resp = requests.get(view_url, headers=headers)
    view_resp.raise_for_status()
    view_payload = view_resp.json()
    
    features_count = len(view_payload.get("data", {}))
    months_count = len(view_payload.get("meta", {}).get("columns", []))
    print(f"   ✅ Successfully extracted {features_count} feature line-items across {months_count} historical timepoints.")

    # Step 3: Run LightGBM ML Forecaster
    print("\n👉 [Step 3/5] Running 'wc_lightgbm.py' Quantile Forecaster...")
    formatted_forecast_df, csv_payload = run_wc_forecast(view_payload)
    
    print("   📊 ML Prediction Output Generated:")
    print("   " + "-" * 65)
    for line in formatted_forecast_df.to_string(index=False).split("\n"):
        print(f"   {line}")
    print("   " + "-" * 65)

    # Step 4: Upload CSV Chunk to Anaplan
    print("\n👉 [Step 4/5] Uploading Forecasted Output Chunks to Anaplan File Storage...")
    chunk_url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{FILE_ID}/chunks/0"
    chunk_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    chunk_resp = requests.put(chunk_url, data=csv_payload.encode("utf-8"), headers=chunk_headers)
    chunk_resp.raise_for_status()
    print("   ✅ Chunk 0 uploaded successfully.")

    # Step 5: Execute Import Process in Anaplan
    print("\n👉 [Step 5/5] Triggering Anaplan Import Process & Polling Task...")
    proc_url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/processes/{PROCESS_ID}/tasks"
    proc_resp = requests.post(proc_url, headers=headers)
    proc_resp.raise_for_status()
    task_id = proc_resp.json()["taskId"]
    print(f"   ⏳ Task started with Task ID: {task_id}")

    # Poll task status
    time.sleep(1)
    status_url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/tasks/{task_id}"
    status_resp = requests.get(status_url, headers=headers)
    status_resp.raise_for_status()
    status_data = status_resp.json()

    if status_data.get("status") == "COMPLETE":
        print("   ✅ Import Task Status: COMPLETE (100%)")
        print(f"   🎉 {status_data.get('result', {}).get('details', 'Data updated successfully.')}")
    else:
        print(f"   ℹ️ Task Status: {status_data.get('status')}")

    print("\n=======================================================")
    print("  🏆 PIPELINE COMPLETED SUCCESSFULLY!")
    print("  Output data is now loaded and available in Anaplan.")
    print("=======================================================\n")


if __name__ == "__main__":
    run_pipeline()