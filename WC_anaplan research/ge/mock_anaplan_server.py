"""
Mock Anaplan API Server v2.0
============================
Simulates Anaplan's standard REST API v2.0 for local testing and CI/CD pipelines.
Includes OAuth2 authentication, Workspace/Model discovery, View data extraction, 
File Chunk uploading, and Process Task execution.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import datetime

app = FastAPI(
    title="Anaplan Mock REST API v2.0",
    description="Simulated Anaplan API server for Workers' Compensation ML Forecasting Pipeline",
    version="2.0.0"
)

# ---------------------------------------------------------
# IN-MEMORY DATABASE / STATE
# ---------------------------------------------------------

MOCK_WORKSPACE_ID = "wrk-insurance-001"
MOCK_MODEL_ID = "mod-wc-pricing-2026"
MOCK_INPUT_VIEW_ID = "view-input-wc-features"
MOCK_OUTPUT_FILE_ID = "file-forecast-output-csv"
MOCK_IMPORT_PROCESS_ID = "proc-import-forecasts"

# Stored token repository
VALID_TOKENS = set(["mock-oauth-token-abc123", "mock-auth-token-uuid-1234"])

# Input features structured directly from user's Excel snapshot (Columns: 1/1/2022, 2/1/2022, 3/1/2022)
INPUT_MODEL_DATA = {
    "columns": ["1/1/2022", "2/1/2022", "3/1/2022"],
    "dimensions": {
        "Region": ["North East", "North East", "North East"],
        "Channel": ["Agency", "Agency", "Agency"],
        "Industry_Class": ["Agriculture", "Agriculture", "Agriculture"],
        "Account_Size": ["Small", "Small", "Small"]
    },
    "features": {
        "Payroll": [54915332.36, 56315326.01, 59848555.91],
        "Employee_Count": [1434, 1357, 1418],
        "Avg_Wage": [47941.17, 49368.42, 49440.05],
        "Payroll_Growth_Rate_YoY": [0.00, 0.09, 0.08],
        "Payroll_Growth_Rate_QoQ": [0.00, 0.03, 0.02],
        "Hazard_Group": [4, 4, 4],
        "Historical_Loss_Ratio": [0.798, 0.841, 0.758],
        "Claim_Frequency": [0.00, 0.00, 0.00],
        "Claim_Severity": [31605, 26910, 27747],
        "Loss_Development_Factor": [1.096, 1.0704, 1.0593],
        "Medical_Inflation_Index": [1.055, 1.0611, 1.0660],
        "Wage_Inflation_Index": [1.030, 1.0355, 1.0413],
        "Employer_Tenure": [5.016, 5.1238, 5.1777],
        "Exposure_Volatility_Score": [0.9302, 2.1805, 1.5953],
        "Filed_Rate_Change": [0.042, 0.041, 0.041],
        "Net_Rate_Achievement": [0.036, 0.038, 0.040],
        "Schedule_Rating_Factor": [0.9747, 1.1174, 1.0064],
        "Renewal_Uplift": [0.063, 0.070, 0.079],
        "Loss_Sensitive_Indicator": [0, 0, 0],
        "Policy_Limit_Change": [1, 0, -1],
        "Class_Code_Reclassification_Freq": [0, 0, 0],
        "Multi_Policy_Bundle_Indicator": [0.39, 0.21, 0.22],
        "Retention_Rate": [0.771, 0.786, 0.823],
        "Churn_Probability": [0.229, 0.215, 0.177],
        "New_Business_Hit_Ratio": [0.276, 0.195, 0.050],
        "Submission_to_Bind_Ratio": [0.175, 0.225, 0.585],
        "Policy_Term_Length": [12, 12, 12],
        "Endorsement_Frequency": [1, 3, 0],
        "Broker_Concentration": [0.046, 0.011, 0.050],
        "Seasonality_Index": [-0.500, -0.3464, -0.1634],
        "Economic_Indicator": [0.650, 0.6298, 0.6144],
        "Employment_Growth_Rate": [0.012, 0.008, 0.015],
        "GWP": [856055.57, 971752.92, 1120470.33]
    }
}

# In-memory file storage for chunk uploads
UPLOADED_FILES = {
    MOCK_OUTPUT_FILE_ID: {
        "name": "wc_forecast_output.csv",
        "chunks": {},
        "is_complete": False
    }
}

# Task status tracker
TASKS = {}

# Stored forecast results once the pipeline imports data
OUTPUT_FORECAST_DATA = {
    "Region": "Mid West",
    "Channel": "Agency",
    "Industry_Class": "Agriculture",
    "Account_Size": "Large",
    "Forecasts": [
        {"Month": "Jan-2026", "P10": 39850.0, "P50": 36879.0, "P90": 47557.0},
        {"Month": "Feb-2026", "P10": 44207.0, "P50": 34222.0, "P90": 48144.0},
        {"Month": "Mar-2026", "P10": 39483.0, "P50": 36949.0, "P90": 44309.0}
    ]
}

# ---------------------------------------------------------
# AUTHENTICATION HELPER
# ---------------------------------------------------------
def verify_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() in ["bearer", "basic", "anaplanauthtoken"]:
        token = parts[1]
        if token in VALID_TOKENS or token.startswith("mock-"):
            return token
            
    # Allow simulated mock tokens
    if authorization.startswith("AnaplanAuthToken ") or "mock" in authorization:
        return authorization
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token"
    )

# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ONLINE",
        "service": "Mock Anaplan REST API Server",
        "version": "2.0",
        "documentation": "/docs"
    }

# 1. OAuth 2.0 Token Generation
@app.post("/oauth2/token")
async def generate_oauth_token(request: Request):
    token = f"mock-oauth-token-{uuid.uuid4().hex[:8]}"
    VALID_TOKENS.add(token)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600
    }

# 2. Workspace Listing
@app.get("/api/2/0/workspaces")
def list_workspaces(authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    return {
        "workspaces": [
            {
                "id": MOCK_WORKSPACE_ID,
                "name": "Insurance Underwriting & Actuarial Planning",
                "active": True,
                "sizeInBytes": 2147483648,
                "currentSizeInBytes": 536870912
            }
        ]
    }

# 3. Model Listing
@app.get("/api/2/0/workspaces/{workspace_id}/models")
def list_models(workspace_id: str, authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    if workspace_id != MOCK_WORKSPACE_ID:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "models": [
            {
                "id": MOCK_MODEL_ID,
                "name": "Workers Compensation Pricing Model 2026",
                "currentWorkspaceId": MOCK_WORKSPACE_ID,
                "isActive": True,
                "lastModified": datetime.datetime.utcnow().isoformat()
            }
        ]
    }

# 4. View Data Endpoint (Extracting Input Data from Anaplan)
@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/views/{view_id}/data")
def get_view_data(workspace_id: str, model_id: str, view_id: str, authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    if workspace_id != MOCK_WORKSPACE_ID or model_id != MOCK_MODEL_ID:
        raise HTTPException(status_code=404, detail="Workspace or Model not found")
        
    return {
        "meta": {
            "viewId": view_id,
            "viewName": "WC Input Feature Grid",
            "columns": INPUT_MODEL_DATA["columns"],
            "dimensions": INPUT_MODEL_DATA["dimensions"]
        },
        "data": INPUT_MODEL_DATA["features"]
    }

# 5. List Files / Chunks metadata
@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files")
def list_files(workspace_id: str, model_id: str, authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    return {
        "files": [
            {
                "id": MOCK_OUTPUT_FILE_ID,
                "name": "wc_forecast_output.csv",
                "chunkCount": 1,
                "delimiter": ",",
                "encoding": "UTF-8",
                "hasHeader": True
            }
        ]
    }

# 6. Upload File Chunk (Pushing ML Model Predictions)
@app.put("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/chunks/{chunk_id}")
async def upload_file_chunk(
    workspace_id: str,
    model_id: str,
    file_id: str,
    chunk_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)
    body_bytes = await request.body()
    chunk_text = body_bytes.decode("utf-8", errors="ignore")
    
    if file_id not in UPLOADED_FILES:
        UPLOADED_FILES[file_id] = {"name": f"file_{file_id}.csv", "chunks": {}, "is_complete": False}
        
    UPLOADED_FILES[file_id]["chunks"][chunk_id] = chunk_text
    UPLOADED_FILES[file_id]["is_complete"] = True
    
    return {
        "status": "SUCCESS",
        "statusMessage": f"Chunk {chunk_id} for file {file_id} received successfully ({len(body_bytes)} bytes)."
    }

# 7. Execute Process (Import Task Trigger)
@app.post("/api/2/0/workspaces/{workspace_id}/models/{model_id}/processes/{process_id}/tasks")
def run_import_process(
    workspace_id: str,
    model_id: str,
    process_id: str,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)
    task_id = f"task-{uuid.uuid4().hex[:6]}"
    TASKS[task_id] = {
        "taskId": task_id,
        "processId": process_id,
        "status": "COMPLETE",
        "progress": 100,
        "successful": True,
        "details": "Forecast predictions loaded and mapped into Output Grid successfully."
    }
    return {
        "taskId": task_id,
        "status": "IN_PROGRESS",
        "createdTime": datetime.datetime.utcnow().isoformat()
    }

# 8. Check Task Status
@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/tasks/{task_id}")
def get_task_status(workspace_id: str, model_id: str, task_id: str, authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    task = TASKS[task_id]
    return {
        "taskId": task["taskId"],
        "status": "COMPLETE",
        "progress": 100,
        "result": {
            "successful": True,
            "objectId": task["processId"],
            "failureDumpAvailable": False,
            "details": task["details"]
        }
    }

# 9. Inspection endpoint to see the final output data stored in Anaplan
@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/forecast-output")
def view_forecast_output(workspace_id: str, model_id: str, authorization: Optional[str] = Header(None)):
    verify_auth(authorization)
    # Check if a file was uploaded
    latest_chunk = UPLOADED_FILES.get(MOCK_OUTPUT_FILE_ID, {}).get("chunks", {}).get("0")
    return {
        "status": "SUCCESS",
        "module": "Forecasted Output Data",
        "active_forecast": OUTPUT_FORECAST_DATA,
        "raw_uploaded_csv": latest_chunk if latest_chunk else "No CSV chunk uploaded yet."
    }

if __name__ == "__main__":
    print("==================================================================")
    print(" 🚀 Starting Anaplan Mock Server on http://localhost:8000")
    print(" Interactive Swagger UI Documentation: http://localhost:8000/docs")
    print("==================================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)