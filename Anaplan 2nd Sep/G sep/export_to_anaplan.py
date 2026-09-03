import os
import requests

SERVER_URL = "http://127.0.0.1:5000"
WORKSPACE_ID = "ws_mock_001"
MODEL_ID = "model_mock_101"
FILE_ID = "processed_output"

LOCAL_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_storage", "processed_outputs")
FILE_NAME = "processed_output.xlsx"
LOCAL_FILE_PATH = os.path.join(LOCAL_OUTPUT_DIR, FILE_NAME)

def run_export():
    if not os.path.exists(LOCAL_FILE_PATH):
        print(f"[ERROR] Source file not found at: {LOCAL_FILE_PATH}")
        print("Run `python generate_sample_data.py` first to create sample data.")
        return

    endpoint = f"{SERVER_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{FILE_ID}/upload"
    print(f"[Export Step] Uploading {LOCAL_FILE_PATH} to: {endpoint}")

    try:
        with open(LOCAL_FILE_PATH, "rb") as file_data:
            files = {"file": (FILE_NAME, file_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            response = requests.post(endpoint, files=files)

        if response.status_code == 200:
            print("[SUCCESS] Server response:")
            print(response.json())
        else:
            print(f"[FAILED] HTTP {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to mock server. Ensure server.py is running on port 5000.")

if __name__ == "__main__":
    run_export()
