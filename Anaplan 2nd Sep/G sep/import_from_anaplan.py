import os
import requests

SERVER_URL = "http://127.0.0.1:5000"
WORKSPACE_ID = "ws_mock_001"
MODEL_ID = "model_mock_101"
FILE_ID = "sample_anaplan_input"

LOCAL_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_storage", "downloaded_inputs")
os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)

def run_import():
    endpoint = f"{SERVER_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{FILE_ID}/download"
    print(f"[Import Step] Requesting file from: {endpoint}")

    try:
        response = requests.get(endpoint, stream=True)
        if response.status_code == 200:
            target_path = os.path.join(LOCAL_DOWNLOAD_DIR, f"{FILE_ID}.xlsx")
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[SUCCESS] Downloaded file from Anaplan and saved to: {target_path}")
        else:
            print(f"[FAILED] HTTP {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to mock server. Ensure server.py is running on port 5000.")

if __name__ == "__main__":
    run_import()
