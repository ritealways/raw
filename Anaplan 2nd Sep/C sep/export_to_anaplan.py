"""
Simulates pushing an Excel file TO Anaplan.

In a real integration, this is where you'd call the Anaplan API to
upload/import data into an Anaplan model. Here, we simply save the
file that comes in (uploaded via Postman) into "data/anaplan_export",
which we're treating as Anaplan's "inbox".

This module is normally called by the server (anaplan_server.py) when
Postman hits:
    POST /api/export-to-anaplan
with a file attached.

You won't usually run this file directly since it needs an uploaded
file object from the server — start the server and use Postman instead
(see README.md for the exact steps).
"""

import os
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_FOLDER = os.path.join(BASE_DIR, "data", "anaplan_export")  # pretend this = Anaplan's inbox


def run_export(uploaded_file):
    """
    uploaded_file: a Flask/werkzeug FileStorage object (comes from request.files
    when a file is uploaded through Postman).

    Saves the file into the mock 'Anaplan export' folder and returns a
    summary dictionary describing what happened.
    """
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = os.path.splitext(uploaded_file.filename)[0]
    new_filename = f"{original_name}_export_{timestamp}.xlsx"
    destination_path = os.path.join(EXPORT_FOLDER, new_filename)

    uploaded_file.save(destination_path)

    # Read it back to confirm it's a valid Excel file and report row/column counts
    df = pd.read_excel(destination_path)

    return {
        "status": "success",
        "message": "File exported to (mock) Anaplan successfully.",
        "saved_to": destination_path,
        "rows": len(df),
        "columns": list(df.columns),
    }


if __name__ == "__main__":
    print("This script is designed to be called by anaplan_server.py")
    print("when a file is uploaded through Postman.")
    print("To test it, start the server (python anaplan_server.py) and")
    print("use the 'Export to Anaplan' request in Postman.")
