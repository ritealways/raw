"""
pipeline.py
------------------------------------------------------------
END-TO-END PIPELINE SCRIPT

WHAT THIS DOES, STEP BY STEP:
    STEP 1  Log in to the mock Anaplan server
    STEP 2  Download ("export") input_excel.xlsx from the mock Anaplan server
    STEP 3  Run YOUR existing wc_lgbm.py on that file to produce Output_excel.xlsx
            (this script does NOT do any forecasting itself - it just calls
             your wc_lgbm.py the same way you'd run it normally)
    STEP 4  Upload ("import") the resulting Output_excel.xlsx back to the
            mock Anaplan server
    STEP 5  Download it back out again to confirm it saved correctly

This script does not generate, invent, or touch any data itself - it only
moves your real files back and forth and calls your real forecasting
script in the middle.

Run it with:
    python pipeline.py

Requires mock_server.py to already be running (see README.md).
------------------------------------------------------------
============  >>>  EDIT THIS SECTION TO MATCH YOUR SETUP  <<<  ============
------------------------------------------------------------
"""

import os
import subprocess
import sys

BASE_URL = "http://127.0.0.1:8000"          # must match the port mock_server.py runs on

WC_LGBM_SCRIPT_PATH = "./wc_lgbm.py"         # path to YOUR forecasting script

# Where this pipeline will temporarily save the file it pulls from Anaplan,
# and where it expects wc_lgbm.py to write its result. These are just local
# working file names for the handoff between "download" and "your script".
PULLED_INPUT_PATH = "./data/pulled_input_excel.xlsx"
GENERATED_OUTPUT_PATH = "./data/generated_output_excel.xlsx"

# ------------------------------------------------------------
# HOW YOUR wc_lgbm.py GETS CALLED
# ------------------------------------------------------------
# By default this assumes your script can be run from the command line like:
#     python wc_lgbm.py --input pulled_input_excel.xlsx --output generated_output_excel.xlsx
#
# If your script uses different flags/positional arguments, or hardcodes its
# own file paths, edit the `call_wc_lgbm()` function below - there are two
# ready-made options in there (command-line call, or import-as-a-function)
# with instructions. You only need to set this up once.
# ------------------------------------------------------------


def call_wc_lgbm(input_path: str, output_path: str):
    """
    Calls your existing wc_lgbm.py forecasting script.

    OPTION A (default, active): run it as a command-line program, passing
    the input and output file paths as arguments.

    OPTION B (commented out below): import it as a Python module and call
    a function inside it directly. Use this if wc_lgbm.py is written as
    importable functions rather than a script you run from the terminal.
    """

    # ---------------- OPTION A: command-line call ----------------
    cmd = [
        sys.executable, WC_LGBM_SCRIPT_PATH,
        "--input", input_path,
        "--output", output_path,
    ]
    log(f"Calling your forecasting script: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            "wc_lgbm.py did not run successfully (see error output above).\n"
            "If your script expects different command-line arguments than "
            "'--input <path> --output <path>', open pipeline.py and edit the "
            "`call_wc_lgbm()` function to match how you normally run wc_lgbm.py."
        )

    # ---------------- OPTION B: import as a module (alternative) ----------------
    # If your wc_lgbm.py is instead meant to be imported (e.g. it defines a
    # function like `run(input_path, output_path)` or `generate_forecast(...)`),
    # comment out OPTION A above and use something like this instead:
    #
    # sys.path.insert(0, os.path.dirname(os.path.abspath(WC_LGBM_SCRIPT_PATH)))
    # import wc_lgbm
    # wc_lgbm.run(input_path, output_path)   # <- replace `run` with your actual function name


# ============================================================
# You normally don't need to touch anything below this line.
# ============================================================

import requests

WORKSPACE_ID = "wrk-001"
MODEL_ID = "mod-101"
INPUT_FILE_ID = "file-201"
OUTPUT_FILE_ID = "file-202"
IMPORT_PROCESS_ID = "proc-301"


def log(msg: str):
    print(f"[pipeline] {msg}")


def login() -> str:
    log("STEP 1: Logging in to mock Anaplan server...")
    resp = requests.post(f"{BASE_URL}/oauth2/token")
    resp.raise_for_status()
    token = resp.json()["access_token"]
    log(f"  -> Got token: {token[:24]}...")
    return token


def download_input_excel(token: str, save_to: str):
    log("STEP 2: Downloading input_excel.xlsx from Anaplan (export)...")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{INPUT_FILE_ID}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    os.makedirs(os.path.dirname(save_to), exist_ok=True)
    with open(save_to, "wb") as f:
        f.write(resp.content)
    log(f"  -> Saved to {save_to} ({len(resp.content)} bytes)")


def push_output_excel(token: str, file_path: str):
    log("STEP 4: Pushing Output_excel.xlsx back to Anaplan (import)...")
    headers = {"Authorization": f"Bearer {token}"}

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # 4a. Upload as chunk "0"
    upload_url = (f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}"
                  f"/files/{OUTPUT_FILE_ID}/chunks/0")
    resp = requests.put(upload_url, headers=headers, data=file_bytes)
    resp.raise_for_status()
    log("  -> Uploaded.")

    # 4b. Trigger the import process
    process_url = (f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}"
                    f"/processes/{IMPORT_PROCESS_ID}/tasks")
    resp = requests.post(process_url, headers=headers)
    resp.raise_for_status()
    task_id = resp.json()["taskId"]
    log(f"  -> Import task started: {task_id} (status: {resp.json()['status']})")


def verify_output(token: str):
    log("STEP 5: Verifying by downloading Output_excel.xlsx back from Anaplan...")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/2/0/workspaces/{WORKSPACE_ID}/models/{MODEL_ID}/files/{OUTPUT_FILE_ID}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    log(f"  -> Confirmed: Anaplan now has an Output_excel.xlsx of {len(resp.content)} bytes stored.")


def main():
    try:
        token = login()
    except requests.exceptions.ConnectionError:
        log("ERROR: Could not connect to the mock Anaplan server.")
        log(f"       Make sure mock_server.py is running at {BASE_URL} (see README.md).")
        sys.exit(1)

    try:
        download_input_excel(token, PULLED_INPUT_PATH)
    except requests.exceptions.HTTPError as e:
        log(f"ERROR downloading input file: {e}")
        log("       Check that INPUT_EXCEL_PATH in mock_server.py points at your real input_excel.xlsx.")
        sys.exit(1)

    log("STEP 3: Running your wc_lgbm.py forecasting script...")
    call_wc_lgbm(PULLED_INPUT_PATH, GENERATED_OUTPUT_PATH)

    if not os.path.exists(GENERATED_OUTPUT_PATH):
        log(f"ERROR: expected wc_lgbm.py to create '{GENERATED_OUTPUT_PATH}' but it wasn't found.")
        log("       Check that your script actually writes its result to the --output path given to it.")
        sys.exit(1)
    log(f"  -> wc_lgbm.py finished. Output file created at {GENERATED_OUTPUT_PATH}")

    push_output_excel(token, GENERATED_OUTPUT_PATH)
    verify_output(token)

    log("Done. Input pulled from Anaplan -> forecast generated by wc_lgbm.py -> pushed back to Anaplan.")


if __name__ == "__main__":
    main()
