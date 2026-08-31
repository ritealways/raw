"""
MOCK ANAPLAN SERVER
--------------------
This is a tiny fake version of Anaplan that runs on your own laptop.
It does NOT connect to the real Anaplan. It just pretends to be Anaplan
so you can test your Postman + Streamlit workflow end to end.

It can:
  1. Receive a CSV from Postman  (pretend: "Anaplan has data ready for us")
  2. Hand that CSV to our pull script (pretend: "we export data FROM Anaplan")
  3. Receive the forecast output from our push script (pretend: "we push results INTO Anaplan")
  4. Let Postman check what was received (pretend: "verify Anaplan got the forecast")

Run it with:   python anaplan_mock_server.py
It will start on:  http://localhost:5000
"""

from flask import Flask, request, send_file, jsonify
import os

app = Flask(__name__)

# Folder where this fake server "stores" its files
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

INPUT_FILE = os.path.join(STORAGE_DIR, "anaplan_input.csv")
OUTPUT_FILE = os.path.join(STORAGE_DIR, "anaplan_output.csv")


@app.route("/anaplan/status", methods=["GET"])
def status():
    """Simple health check so you know the server is alive."""
    return jsonify({
        "status": "running",
        "input_file_present": os.path.exists(INPUT_FILE),
        "output_file_present": os.path.exists(OUTPUT_FILE),
    })


@app.route("/anaplan/upload-input", methods=["POST"])
def upload_input():
    """
    Step used by Postman ONCE, to simulate 'Anaplan has source data ready'.
    Postman sends a CSV file here (form-data, key = 'file').
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part called 'file' in the request"}), 400
    f = request.files["file"]
    f.save(INPUT_FILE)
    return jsonify({"message": "Input data received by mock Anaplan.", "saved_as": INPUT_FILE})


@app.route("/anaplan/get-input", methods=["GET"])
def get_input():
    """
    Our pull script calls this to 'export data FROM Anaplan'.
    Returns the CSV file that was uploaded earlier.
    """
    if not os.path.exists(INPUT_FILE):
        return jsonify({"error": "No input file uploaded yet. Use /anaplan/upload-input first."}), 404
    return send_file(INPUT_FILE, as_attachment=True, download_name="input.csv")


@app.route("/anaplan/push-output", methods=["POST"])
def push_output():
    """
    Our push script (or Postman) calls this to 'push forecast results INTO Anaplan'.
    Expects a CSV file (form-data, key = 'file').
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part called 'file' in the request"}), 400
    f = request.files["file"]
    f.save(OUTPUT_FILE)
    return jsonify({"message": "Forecast output received by mock Anaplan.", "saved_as": OUTPUT_FILE})


@app.route("/anaplan/get-output", methods=["GET"])
def get_output():
    """
    Postman can call this to double check the forecast actually arrived,
    just like checking a module in real Anaplan.
    """
    if not os.path.exists(OUTPUT_FILE):
        return jsonify({"error": "No output file received yet."}), 404
    return send_file(OUTPUT_FILE, as_attachment=True, download_name="output.csv")


if __name__ == "__main__":
    print("Mock Anaplan server starting at http://localhost:5000")
    print("Storage folder:", STORAGE_DIR)
    app.run(host="0.0.0.0", port=5000, debug=True)
