"""
PULL FROM ANAPLAN
------------------
This script asks the mock Anaplan server for its input data and saves it
locally as data/input.csv, so you can then drag that file into your
Streamlit app (app.py) exactly like the screenshot showed.

Run it with:   python pull_from_anaplan.py
(Make sure anaplan_mock_server.py is already running in another terminal.)
"""

import os
import requests

SERVER_URL = "http://localhost:5000/anaplan/get-input"
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "input.csv")

def main():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    print(f"Requesting input data from mock Anaplan at {SERVER_URL} ...")
    response = requests.get(SERVER_URL)

    if response.status_code != 200:
        print("Failed to pull data. Server said:")
        print(response.text)
        return

    with open(SAVE_PATH, "wb") as f:
        f.write(response.content)

    print(f"Success! Input data saved to: {SAVE_PATH}")
    print("Next step: open your Streamlit app and drag this file in.")

if __name__ == "__main__":
    main()
