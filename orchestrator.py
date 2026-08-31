"""
ORCHESTRATOR — automates your EXISTING app.py with ZERO code changes to it.

What this does, step by step:
  1. Downloads input.csv from the mock Anaplan server.
  2. Opens your already-running Streamlit app in a real Chrome window
     (via Selenium) and uploads that file into the SAME drag-and-drop
     box you use manually — no code in app.py is touched.
  3. Watches a folder on disk for output.csv to appear or change.
  4. As soon as it does, pushes it to the mock Anaplan server.

REQUIREMENTS (install once):
    pip install selenium webdriver-manager requests

You must ALSO have:
  - anaplan_mock_server.py running (uvicorn ... --port 8000)
  - app.py running via `streamlit run app.py` (usually http://localhost:8501)
  - Google Chrome installed on your machine
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ---------- EDIT THESE 3 LINES TO MATCH YOUR SETUP ----------
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_WATCH_FOLDER = os.path.dirname(os.path.abspath(__file__))  # folder where app.py saves output.csv
OUTPUT_FILENAME = "output.csv"
# --------------------------------------------------------------

ANAPLAN_BASE_URL = "http://127.0.0.1:8000"
LOCAL_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.csv")


def fetch_input_from_anaplan():
    print("Step 1: Fetching input.csv from mock Anaplan...")
    r = requests.get(f"{ANAPLAN_BASE_URL}/anaplan/input", timeout=30)
    r.raise_for_status()
    with open(LOCAL_INPUT_PATH, "wb") as f:
        f.write(r.content)
    print(f"  -> saved to {LOCAL_INPUT_PATH}")
    return LOCAL_INPUT_PATH


def upload_via_browser(file_path):
    print("Step 2: Opening Streamlit app in Chrome and uploading file...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(STREAMLIT_URL)
    time.sleep(4)  # let the page fully load

    # Streamlit's drag-and-drop box is backed by a hidden <input type="file">
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(file_path)
    print("  -> file sent to the uploader, app is now processing it")
    print("  -> leaving the browser window open so the app can run its pipeline")
    print("  -> (if your app needs you to click Run/Model/Dashboard buttons, do that now in the opened window)")
    return driver


def wait_for_output(timeout_seconds=600):
    print("Step 3: Watching for output.csv ...")
    output_path = os.path.join(OUTPUT_WATCH_FOLDER, OUTPUT_FILENAME)
    seen_mtime = os.path.getmtime(output_path) if os.path.exists(output_path) else None
    start = time.time()

    while time.time() - start < timeout_seconds:
        if os.path.exists(output_path):
            current_mtime = os.path.getmtime(output_path)
            if seen_mtime is None or current_mtime > seen_mtime:
                print(f"  -> detected new/updated {OUTPUT_FILENAME}")
                time.sleep(2)  # small buffer to let the file finish writing
                return output_path
        time.sleep(3)

    raise TimeoutError(f"No {OUTPUT_FILENAME} appeared in {OUTPUT_WATCH_FOLDER} within {timeout_seconds} seconds.")


def push_output_to_anaplan(output_path):
    print("Step 4: Pushing output.csv to mock Anaplan...")
    with open(output_path, "rb") as f:
        files = {"file": (OUTPUT_FILENAME, f, "text/csv")}
        r = requests.post(f"{ANAPLAN_BASE_URL}/anaplan/output", files=files, timeout=30)
    r.raise_for_status()
    print("  -> success:", r.json())


if __name__ == "__main__":
    input_path = fetch_input_from_anaplan()
    driver = upload_via_browser(input_path)
    try:
        output_path = wait_for_output()
        push_output_to_anaplan(output_path)
        print("\nDONE. Full loop complete: Anaplan -> Streamlit -> Anaplan.")
    finally:
        input("\nPress Enter to close the browser window...")
        driver.quit()
