import os
import sys
import subprocess

INPUT_FILE = "input_excel.xlsx"
OUTPUT_FILE = "Output_excel.xlsx"
MODEL_SCRIPT = "wc_lgbm.py"

def run_pipeline():
    """
    Pipeline orchestrator that verifies input data, executes your wc_lgbm.py script,
    and checks for output excel generation.
    """
    print(f"[PIPELINE] Checking for input file '{INPUT_FILE}'...")
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Required input file '{INPUT_FILE}' is missing.")
        sys.exit(1)
    
    print(f"[PIPELINE] Found '{INPUT_FILE}'. Launching forecasting model '{MODEL_SCRIPT}'...")

    if not os.path.exists(MODEL_SCRIPT):
        print(f"[ERROR] Forecasting script '{MODEL_SCRIPT}' not found in current directory.")
        sys.exit(1)

    try:
        # Executes wc_lgbm.py using the current Python execution environment
        process = subprocess.run(
            [sys.executable, MODEL_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[MODEL STDOUT]: {process.stdout.strip()}")
    except subprocess.CalledProcessError as err:
        print(f"[ERROR] '{MODEL_SCRIPT}' failed with exit code {err.returncode}:")
        print(err.stderr)
        sys.exit(1)

    print(f"[PIPELINE] Verifying output file '{OUTPUT_FILE}'...")
    if os.path.exists(OUTPUT_FILE):
        print(f"[SUCCESS] Pipeline executed successfully. '{OUTPUT_FILE}' is ready for Anaplan export.")
    else:
        print(f"[ERROR] Forecasting script completed but '{OUTPUT_FILE}' was not created.")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()