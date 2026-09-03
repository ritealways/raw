"""
Mock Anaplan Integration Server
--------------------------------
This is a simple Flask server that pretends to be a bridge between
your system and Anaplan. It exposes two web addresses (endpoints)
that Postman will call:

1. POST /api/import-from-anaplan
   - Pretends to pull an Excel file FROM Anaplan.
   - In real life this would call Anaplan's API. Here, it just reads
     an Excel file sitting in the "data/anaplan_source" folder (which
     is standing in for Anaplan) and copies it into "data/imported".

2. POST /api/export-to-anaplan
   - Pretends to push an Excel file TO Anaplan.
   - You upload a file in Postman (form-data), and the server saves it
     into the "data/anaplan_export" folder (which is standing in for
     Anaplan's inbox).

There is also a GET /health endpoint so you can quickly check the
server is alive by visiting it in a browser.

HOW TO RUN THIS FILE:
    python anaplan_server.py

Then leave this terminal window open and running while you test
things from Postman. Full step-by-step instructions are in README.md.
"""

import os
from flask import Flask, request, jsonify

from import_from_anaplan import run_import
from export_to_anaplan import run_export

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/health", methods=["GET"])
def health():
    """Simple check to confirm the server is up. Visit in a browser:
    http://127.0.0.1:5000/health
    """
    return jsonify({"status": "ok", "message": "Mock Anaplan server is running"}), 200


@app.route("/api/import-from-anaplan", methods=["POST"])
def import_from_anaplan_endpoint():
    """Called from Postman. No file needs to be attached — this pretends
    to reach into Anaplan and pull down the latest export automatically.
    """
    try:
        result = run_import()
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/export-to-anaplan", methods=["POST"])
def export_to_anaplan_endpoint():
    """Called from Postman with an Excel file attached (form-data, key = 'file').
    Pretends to push that file into Anaplan.
    """
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file found. In Postman, use Body -> form-data, "
                        "key = 'file', type = File, and attach an .xlsx file."
        }), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename."}), 400

    try:
        result = run_export(uploaded_file)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("=" * 70)
    print(" Mock Anaplan Server starting...")
    print(" Health check:  http://127.0.0.1:5000/health")
    print(" Import:        POST http://127.0.0.1:5000/api/import-from-anaplan")
    print(" Export:        POST http://127.0.0.1:5000/api/export-to-anaplan")
    print(" Press CTRL+C in this terminal to stop the server.")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
