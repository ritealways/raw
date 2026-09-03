import os
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANAPLAN_INPUT_DIR = os.path.join(BASE_DIR, "anaplan_storage", "input_source")
ANAPLAN_EXPORT_DIR = os.path.join(BASE_DIR, "anaplan_storage", "export_target")

os.makedirs(ANAPLAN_INPUT_DIR, exist_ok=True)
os.makedirs(ANAPLAN_EXPORT_DIR, exist_ok=True)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Mock Anaplan Integration Server",
        "version": "1.0.0"
    }), 200

@app.route("/api/2/0/workspaces/<workspace_id>/models/<model_id>/files/<file_id>/download", methods=["GET"])
def download_file(workspace_id, model_id, file_id):
    """Mocks Anaplan File Download API (read from Anaplan)."""
    for ext in [".xlsx", ".xls", ""]:
        candidate_path = os.path.join(ANAPLAN_INPUT_DIR, f"{file_id}{ext}")
        if os.path.exists(candidate_path):
            return send_file(
                candidate_path,
                as_attachment=True,
                download_name=f"{file_id}.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    return jsonify({
        "error": "File not found in mock Anaplan storage",
        "requested_file_id": file_id,
        "searched_directory": ANAPLAN_INPUT_DIR
    }), 404

@app.route("/api/2/0/workspaces/<workspace_id>/models/<model_id>/files/<file_id>/upload", methods=["POST"])
def upload_file(workspace_id, model_id, file_id):
    """Mocks Anaplan File Upload API (push export into Anaplan)."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request. Use key 'file' in form-data."}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    clean_filename = secure_filename(uploaded_file.filename)
    save_path = os.path.join(ANAPLAN_EXPORT_DIR, clean_filename)
    uploaded_file.save(save_path)

    return jsonify({
        "status": "SUCCESS",
        "message": f"File '{clean_filename}' uploaded successfully to mock Anaplan server.",
        "workspace_id": workspace_id,
        "model_id": model_id,
        "file_id": file_id,
        "anaplan_destination": save_path
    }), 200

if __name__ == "__main__":
    print("Starting Mock Anaplan Server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
