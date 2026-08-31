"""
ANAPLAN CLIENT HELPERS
-----------------------
Small helper functions that your Streamlit app (app.py) will call.
Import these into app.py like this:

    from anaplan_client import fetch_input_from_anaplan, push_output_to_anaplan

They just wrap simple HTTP requests to the mock Anaplan server
(anaplan_mock_server.py), which must already be running on port 8000.
"""

import requests

ANAPLAN_BASE_URL = "http://127.0.0.1:8000"


def fetch_input_from_anaplan(save_path: str = "input.csv") -> str:
    """
    Downloads input.csv from the mock Anaplan server and saves it
    locally so the rest of app.py (your existing data-loading code)
    can use it exactly like a manually uploaded file.

    Returns the local file path on success, raises an Exception on failure.
    """
    response = requests.get(f"{ANAPLAN_BASE_URL}/anaplan/input", timeout=30)
    if response.status_code != 200:
        raise Exception(f"Could not fetch input from Anaplan: {response.text}")

    with open(save_path, "wb") as f:
        f.write(response.content)

    return save_path


def push_output_to_anaplan(local_file_path: str = "output.csv") -> dict:
    """
    Uploads your generated output.csv (the forecasting results)
    to the mock Anaplan server.

    Returns the server's JSON response on success, raises an Exception on failure.
    """
    with open(local_file_path, "rb") as f:
        files = {"file": (local_file_path, f, "text/csv")}
        response = requests.post(f"{ANAPLAN_BASE_URL}/anaplan/output", files=files, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Could not push output to Anaplan: {response.text}")

    return response.json()


def anaplan_status() -> dict:
    """Quick check of what files currently exist in the mock Anaplan."""
    response = requests.get(f"{ANAPLAN_BASE_URL}/anaplan/status", timeout=10)
    response.raise_for_status()
    return response.json()
