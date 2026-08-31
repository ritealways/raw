"""
PUSH TO ANAPLAN
-----------------
This script takes the output.csv that your Streamlit app generated
(the forecast results) and pushes it to the mock Anaplan server,
simulating writing results back into Anaplan.

Run it with:   python push_to_anaplan.py
(Make sure anaplan_mock_server.py is already running in another terminal,
 and that data/output.csv exists — export it from your Streamlit app first.)
"""

import os
import requests

SERVER_URL = "http://localhost:5000/anaplan/push-output"
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output.csv")

def main():
    if not os.path.exists(OUTPUT_PATH):
        print(f"Could not find {OUTPUT_PATH}")
        print("Export/save your Streamlit app's forecast results as data/output.csv first.")
        return

    print(f"Pushing {OUTPUT_PATH} to mock Anaplan at {SERVER_URL} ...")
    with open(OUTPUT_PATH, "rb") as f:
        files = {"file": ("output.csv", f, "text/csv")}
        response = requests.post(SERVER_URL, files=files)

    if response.status_code == 200:
        print("Success! Mock Anaplan response:")
        print(response.json())
    else:
        print("Failed to push data. Server said:")
        print(response.text)

if __name__ == "__main__":
    main()
