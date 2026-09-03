"""
Mock Anaplan Server - A simple Flask REST API that simulates Anaplan integration.
This server provides endpoints to:
1. Upload/Import Excel files (simulating import from Anaplan)
2. Download/Export Excel files (simulating export to Anaplan)
3. List available files
4. Check server status

Run: python server.py
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for Postman access

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "input_from_anaplan")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_to_anaplan")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed_data")
LOG_FILE = os.path.join(BASE_DIR, "server_logs.json")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(action, filename, status, message=""):
    """Log all server activities to a JSON file"""
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "filename": filename,
        "status": status,
        "message": message
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append(log_entry)

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

# ==================== HEALTH CHECK ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    return jsonify({
        "status": "healthy",
        "message": "Mock Anaplan Server is running!",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "import": "POST /api/import",
            "export": "GET /api/export/<filename>",
            "list_input": "GET /api/files/input",
            "list_output": "GET /api/files/output",
            "upload_output": "POST /api/export/upload"
        }
    }), 200

# ==================== IMPORT FROM ANAPLAN ====================
@app.route('/api/import', methods=['POST'])
def import_from_anaplan():
    """
    Import Excel file from Anaplan (mock)
    Saves the uploaded file to input_from_anaplan folder

    Postman: POST http://localhost:5000/api/import
    Body: form-data, key="file", value=choose your excel file
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            log_activity("IMPORT", "", "FAILED", "No file part in request")
            return jsonify({
                "success": False,
                "message": "No file part in the request. Use key 'file' in form-data."
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            log_activity("IMPORT", "", "FAILED", "No file selected")
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        # Validate file extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(INPUT_FOLDER, saved_filename)

            # Save the file
            file.save(filepath)

            # Read and log file info
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)

                row_count = len(df)
                column_count = len(df.columns)
                columns = list(df.columns)

                log_activity("IMPORT", saved_filename, "SUCCESS", 
                           f"Rows: {row_count}, Columns: {column_count}")

                return jsonify({
                    "success": True,
                    "message": f"File imported successfully from Anaplan!",
                    "filename": saved_filename,
                    "original_name": filename,
                    "saved_path": filepath,
                    "file_info": {
                        "rows": row_count,
                        "columns": column_count,
                        "column_names": columns
                    },
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }), 200

            except Exception as e:
                log_activity("IMPORT", saved_filename, "PARTIAL", str(e))
                return jsonify({
                    "success": True,
                    "message": "File saved but could not read contents",
                    "filename": saved_filename,
                    "warning": str(e)
                }), 200
        else:
            log_activity("IMPORT", file.filename, "FAILED", "Invalid file type")
            return jsonify({
                "success": False,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

    except Exception as e:
        log_activity("IMPORT", "", "ERROR", str(e))
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/files/input', methods=['GET'])
def list_input_files():
    """
    List all imported files (input from Anaplan)

    Postman: GET http://localhost:5000/api/files/input
    """
    try:
        files = []
        for filename in os.listdir(INPUT_FOLDER):
            filepath = os.path.join(INPUT_FOLDER, filename)
            if os.path.isfile(filepath):
                file_stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size_bytes": file_stat.st_size,
                    "size_kb": round(file_stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

        return jsonify({
            "success": True,
            "folder": "input_from_anaplan",
            "file_count": len(files),
            "files": sorted(files, key=lambda x: x["modified"], reverse=True)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==================== EXPORT TO ANAPLAN ====================
@app.route('/api/export/upload', methods=['POST'])
def upload_output_file():
    """
    Upload output file to Anaplan (mock)
    Saves the uploaded file to output_to_anaplan folder

    Postman: POST http://localhost:5000/api/export/upload
    Body: form-data, key="file", value=choose your excel file
    """
    try:
        if 'file' not in request.files:
            log_activity("EXPORT_UPLOAD", "", "FAILED", "No file part")
            return jsonify({
                "success": False,
                "message": "No file part in the request"
            }), 400

        file = request.files['file']

        if file.filename == '':
            log_activity("EXPORT_UPLOAD", "", "FAILED", "No file selected")
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(OUTPUT_FOLDER, saved_filename)

            file.save(filepath)

            log_activity("EXPORT_UPLOAD", saved_filename, "SUCCESS", "File uploaded to Anaplan mock")

            return jsonify({
                "success": True,
                "message": "File successfully exported to Anaplan (mock)!",
                "filename": saved_filename,
                "original_name": filename,
                "saved_path": filepath,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 200
        else:
            log_activity("EXPORT_UPLOAD", file.filename, "FAILED", "Invalid file type")
            return jsonify({
                "success": False,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

    except Exception as e:
        log_activity("EXPORT_UPLOAD", "", "ERROR", str(e))
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/export/<filename>', methods=['GET'])
def export_to_anaplan(filename):
    """
    Download a file from output folder (simulating export to Anaplan)

    Postman: GET http://localhost:5000/api/export/filename.xlsx
    """
    try:
        filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))

        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "message": f"File '{filename}' not found in output folder"
            }), 404

        log_activity("EXPORT_DOWNLOAD", filename, "SUCCESS", "File downloaded")

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        log_activity("EXPORT_DOWNLOAD", filename, "ERROR", str(e))
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/files/output', methods=['GET'])
def list_output_files():
    """
    List all exported files (output to Anaplan)

    Postman: GET http://localhost:5000/api/files/output
    """
    try:
        files = []
        for filename in os.listdir(OUTPUT_FOLDER):
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            if os.path.isfile(filepath):
                file_stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size_bytes": file_stat.st_size,
                    "size_kb": round(file_stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

        return jsonify({
            "success": True,
            "folder": "output_to_anaplan",
            "file_count": len(files),
            "files": sorted(files, key=lambda x: x["modified"], reverse=True)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==================== PROCESS DATA (BONUS) ====================
@app.route('/api/process/<filename>', methods=['POST'])
def process_file(filename):
    """
    Process an imported file and create output
    This simulates the business logic between import and export

    Postman: POST http://localhost:5000/api/process/filename.xlsx
    Body: JSON with processing options
    """
    try:
        input_filepath = os.path.join(INPUT_FOLDER, secure_filename(filename))

        if not os.path.exists(input_filepath):
            return jsonify({
                "success": False,
                "message": f"File '{filename}' not found in input folder"
            }), 404

        # Read the input file
        if filename.endswith('.csv'):
            df = pd.read_csv(input_filepath)
        else:
            df = pd.read_excel(input_filepath)

        # Simple processing: add a processed column
        df['processed_date'] = datetime.now().strftime("%Y-%m-%d")
        df['processed_by'] = "Mock Anaplan Server"
        df['row_id'] = range(1, len(df) + 1)

        # Save processed file
        output_filename = f"processed_{filename}"
        if output_filename.endswith('.csv'):
            output_filename = output_filename.replace('.csv', '.xlsx')

        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        df.to_excel(output_filepath, index=False)

        log_activity("PROCESS", filename, "SUCCESS", f"Processed to {output_filename}")

        return jsonify({
            "success": True,
            "message": "File processed successfully!",
            "input_file": filename,
            "output_file": output_filename,
            "output_path": output_filepath,
            "rows_processed": len(df),
            "columns_added": ['processed_date', 'processed_by', 'row_id']
        }), 200

    except Exception as e:
        log_activity("PROCESS", filename, "ERROR", str(e))
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==================== VIEW LOGS ====================
@app.route('/api/logs', methods=['GET'])
def view_logs():
    """View server activity logs"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
            return jsonify({
                "success": True,
                "total_logs": len(logs),
                "logs": logs[-50:]  # Return last 50 logs
            }), 200
        else:
            return jsonify({
                "success": True,
                "message": "No logs yet",
                "logs": []
            }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    print("=" * 60)
    print("  MOCK ANAPLAN SERVER")
    print("=" * 60)
    print(f"Server starting at: http://localhost:5000")
    print(f"Input folder:  {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Processed folder: {PROCESSED_FOLDER}")
    print("=" * 60)
    print("Available endpoints:")
    print("  GET  /api/health          - Check server status")
    print("  POST /api/import          - Import file from Anaplan")
    print("  GET  /api/files/input     - List imported files")
    print("  POST /api/export/upload   - Upload file to Anaplan")
    print("  GET  /api/export/<file>   - Download file (export)")
    print("  GET  /api/files/output    - List exported files")
    print("  POST /api/process/<file>  - Process a file")
    print("  GET  /api/logs            - View activity logs")
    print("=" * 60)
    print("Press CTRL+C to stop the server")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
