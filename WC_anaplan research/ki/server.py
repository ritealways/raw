"""
Mock Anaplan Server - Flask API for Workers Compensation Forecasting
This server mimics Anaplan's REST API behavior for integration testing.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime

# Add models directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
from wc_lightgbm import run_forecast

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage (simulating Anaplan's data store)
DATA_STORE = {
    'input_data': [],
    'forecast_output': [],
    'models': {},
    'imports': {},
    'exports': {}
}

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/', methods=['GET'])
def home():
    """Root endpoint - server status."""
    return jsonify({
        'status': 'Mock Anaplan Server is Running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': 'GET /api/health',
            'upload_input': 'POST /api/anaplan/upload-input',
            'run_forecast': 'POST /api/anaplan/run-forecast',
            'get_forecast': 'GET /api/anaplan/forecast-output',
            'push_output': 'POST /api/anaplan/push-output',
            'get_all_data': 'GET /api/anaplan/all-data',
            'clear_data': 'DELETE /api/anaplan/clear'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'server': 'Mock Anaplan Server',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# =============================================================================
# ANAPLAN-LIKE API ENDPOINTS
# =============================================================================

@app.route('/api/anaplan/upload-input', methods=['POST'])
def upload_input():
    """
    Upload input data to the mock Anaplan server.

    Expected JSON Body:
    {
        "data": [
            {
                "Month": "2022-01-01",
                "Region": "North East",
                "Channel": "Agency",
                "Industry_Class": "Agriculture",
                "Account_Size": "Small",
                "Payroll": 54915332.36,
                ... (all other fields from image)
            },
            ...
        ]
    }

    Returns:
        { "status": "success", "records_uploaded": 3, "import_id": "imp_xxx" }
    """
    try:
        payload = request.get_json()

        if not payload or 'data' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing "data" field in request body'
            }), 400

        input_data = payload['data']

        if not isinstance(input_data, list):
            return jsonify({
                'status': 'error',
                'message': '"data" must be a list of records'
            }), 400

        # Store the input data
        import_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        DATA_STORE['input_data'] = input_data
        DATA_STORE['imports'][import_id] = {
            'id': import_id,
            'timestamp': datetime.now().isoformat(),
            'records': len(input_data),
            'status': 'completed'
        }

        return jsonify({
            'status': 'success',
            'message': f'Successfully uploaded {len(input_data)} records',
            'records_uploaded': len(input_data),
            'import_id': import_id,
            'anaplan_style_response': {
                'taskId': import_id,
                'taskState': 'COMPLETE',
                'result': {
                    'successful': len(input_data),
                    'failed': 0,
                    'details': 'All records imported successfully'
                }
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/anaplan/run-forecast', methods=['POST'])
def run_forecast_endpoint():
    """
    Run the wc_lightgbm forecasting model on uploaded input data.

    Expected JSON Body (optional - uses stored data if empty):
    {
        "data": [ ... input records ... ]  // Optional: pass data directly
    }

    OR empty body to use previously uploaded data.

    Returns:
    {
        "status": "success",
        "forecast": [
            {
                "Month": "Jan-2026",
                "Region": "Mid West",
                "Channel": "Agency",
                "Industry_Class": "Agriculture",
                "Account_Size": "Large",
                "P10": 33650.00,
                "P50": 36878.00,
                "P90": 47557.00
            },
            ...
        ]
    }
    """
    try:
        payload = request.get_json() or {}

        # Use provided data or stored data
        if 'data' in payload and payload['data']:
            input_data = payload['data']
        elif DATA_STORE['input_data']:
            input_data = DATA_STORE['input_data']
        else:
            return jsonify({
                'status': 'error',
                'message': 'No input data found. Please upload data first using /api/anaplan/upload-input'
            }), 400

        # Run the forecasting model
        print(f"[SERVER] Running forecast on {len(input_data)} records...")
        forecast_result = run_forecast(input_data)

        # Store the output
        model_run_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        DATA_STORE['forecast_output'] = forecast_result
        DATA_STORE['models'][model_run_id] = {
            'id': model_run_id,
            'timestamp': datetime.now().isoformat(),
            'input_records': len(input_data),
            'output_records': len(forecast_result),
            'status': 'completed'
        }

        return jsonify({
            'status': 'success',
            'message': f'Forecast generated successfully for {len(forecast_result)} months',
            'model_run_id': model_run_id,
            'forecast': forecast_result,
            'anaplan_style_response': {
                'taskId': model_run_id,
                'taskState': 'COMPLETE',
                'result': {
                    'successful': len(forecast_result),
                    'failed': 0,
                    'details': 'Forecast model executed successfully'
                }
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/anaplan/forecast-output', methods=['GET'])
def get_forecast_output():
    """
    Retrieve the generated forecast output.

    Returns:
    {
        "status": "success",
        "forecast": [ ... forecast records ... ]
    }
    """
    if not DATA_STORE['forecast_output']:
        return jsonify({
            'status': 'error',
            'message': 'No forecast output available. Run forecast first using /api/anaplan/run-forecast'
        }), 404

    return jsonify({
        'status': 'success',
        'forecast': DATA_STORE['forecast_output'],
        'record_count': len(DATA_STORE['forecast_output'])
    })


@app.route('/api/anaplan/push-output', methods=['POST'])
def push_output():
    """
    Push forecast output to Anaplan (simulated).
    In real Anaplan, this would write to a module/list.

    Expected JSON Body:
    {
        "target_module": "Forecast_Output_Module",  // Optional
        "data": [ ... forecast records ... ]  // Optional: uses stored forecast if empty
    }

    Returns:
    {
        "status": "success",
        "message": "Output pushed to Anaplan module",
        "export_id": "exp_xxx"
    }
    """
    try:
        payload = request.get_json() or {}
        target_module = payload.get('target_module', 'Forecast_Output_Module')

        # Use provided data or stored forecast
        if 'data' in payload and payload['data']:
            output_data = payload['data']
        elif DATA_STORE['forecast_output']:
            output_data = DATA_STORE['forecast_output']
        else:
            return jsonify({
                'status': 'error',
                'message': 'No forecast output to push. Run forecast first.'
            }), 400

        # Simulate pushing to Anaplan
        export_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        DATA_STORE['exports'][export_id] = {
            'id': export_id,
            'timestamp': datetime.now().isoformat(),
            'target_module': target_module,
            'records': len(output_data),
            'data': output_data,
            'status': 'completed'
        }

        return jsonify({
            'status': 'success',
            'message': f'Successfully pushed {len(output_data)} records to Anaplan module "{target_module}"',
            'export_id': export_id,
            'target_module': target_module,
            'records_pushed': len(output_data),
            'anaplan_style_response': {
                'taskId': export_id,
                'taskState': 'COMPLETE',
                'result': {
                    'successful': len(output_data),
                    'failed': 0,
                    'targetModule': target_module
                }
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/anaplan/all-data', methods=['GET'])
def get_all_data():
    """Get all stored data (for debugging)."""
    return jsonify({
        'status': 'success',
        'input_data': DATA_STORE['input_data'],
        'forecast_output': DATA_STORE['forecast_output'],
        'imports': list(DATA_STORE['imports'].keys()),
        'models': list(DATA_STORE['models'].keys()),
        'exports': list(DATA_STORE['exports'].keys())
    })


@app.route('/api/anaplan/clear', methods=['DELETE'])
def clear_data():
    """Clear all stored data."""
    DATA_STORE['input_data'] = []
    DATA_STORE['forecast_output'] = []
    DATA_STORE['imports'] = {}
    DATA_STORE['models'] = {}
    DATA_STORE['exports'] = {}

    return jsonify({
        'status': 'success',
        'message': 'All data cleared successfully'
    })


# =============================================================================
# ANAPLAN AUTH SIMULATION (Optional)
# =============================================================================

@app.route('/api/anaplan/auth', methods=['POST'])
def anaplan_auth():
    """Simulate Anaplan authentication."""
    return jsonify({
        'status': 'success',
        'token': 'mock_anaplan_token_12345',
        'expires_at': '2099-12-31T23:59:59Z',
        'message': 'Mock authentication successful'
    })


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  MOCK ANAPLAN SERVER - Workers Compensation Forecasting")
    print("=" * 70)
    print()
    print("  Server starting on: http://localhost:5000")
    print()
    print("  Available Endpoints:")
    print("  - GET  /                    → Server info")
    print("  - GET  /api/health          → Health check")
    print("  - POST /api/anaplan/upload-input   → Upload input data")
    print("  - POST /api/anaplan/run-forecast   → Run wc_lightgbm forecast")
    print("  - GET  /api/anaplan/forecast-output→ Get forecast results")
    print("  - POST /api/anaplan/push-output    → Push output to Anaplan")
    print("  - GET  /api/anaplan/all-data       → View all stored data")
    print("  - DELETE /api/anaplan/clear        → Clear all data")
    print()
    print("=" * 70)

    app.run(host='0.0.0.0', port=5000, debug=True)
