"""
Simulates pulling an Excel export FROM Anaplan.

In a real integration, this is where you'd call the Anaplan API
(or pick up a file Anaplan dropped somewhere) and pull the data in.

Here, we treat the folder "data/anaplan_source" as if it WERE Anaplan.
We read the Excel file sitting there and copy it (with a timestamp)
into "data/imported", so the rest of your pipeline has a clean local
copy to work with.

YOU CAN RUN THIS FILE ON ITS OWN, JUST TO TEST IT:
    python import_from_anaplan.py

Normally, though, it gets triggered automatically by the server
(anaplan_server.py) whenever Postman calls:
    POST /api/import-from-anaplan
"""

import os
import shutil
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(BASE_DIR, "data", "anaplan_source")   # pretend this = Anaplan
IMPORTED_FOLDER = os.path.join(BASE_DIR, "data", "imported")       # where we save what we pulled
SOURCE_FILENAME = "input_data.xlsx"


def run_import():
    """Reads the mock 'Anaplan' export and saves a timestamped copy locally.
    Returns a small summary dictionary describing what happened.
    """
    os.makedirs(IMPORTED_FOLDER, exist_ok=True)

    source_path = os.path.join(SOURCE_FOLDER, SOURCE_FILENAME)
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"Could not find '{SOURCE_FILENAME}' in {SOURCE_FOLDER}. "
            f"Run 'python generate_sample_excel.py' first to create sample data."
        )

    # Read it, just to prove we can process it and to report row/column counts
    df = pd.read_excel(source_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"imported_{timestamp}.xlsx"
    destination_path = os.path.join(IMPORTED_FOLDER, new_filename)

    shutil.copy2(source_path, destination_path)

    return {
        "status": "success",
        "message": "Data imported from (mock) Anaplan successfully.",
        "source_file": source_path,
        "saved_to": destination_path,
        "rows": len(df),
        "columns": list(df.columns),
    }


if __name__ == "__main__":
    result = run_import()
    print(result)
