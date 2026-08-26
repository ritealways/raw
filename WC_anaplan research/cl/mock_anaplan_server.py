"""
mock_anaplan_server.py
------------------------------------------------------------
A SIMPLE MOCK ANAPLAN SERVER (built with FastAPI).

What it pretends to be:
    A tiny slice of the real Anaplan REST API (https://api.anaplan.com/2/0/)
    so that you can build & test an integration WITHOUT having a real
    Anaplan tenant.

What it actually does:
    1. Lets a "client" (our forecasting script, or Postman) log in and
       get a fake Bearer token.
    2. Serves a CSV of synthetic "insurance book" input data - the same
       shape of data shown in the screenshot (Region / Channel /
       Industry_Class / Account_Size / Payroll / Avg_Wage / etc.)
       This simulates Anaplan EXPORTING data out to a downstream system.
    3. Accepts a CSV upload (chunk) containing forecast results
       (Region / Channel / Industry_Class / Account_Size / Month /
        P10 / P50 / P90) and "runs an import process" to load it into
       the mock model. This simulates pushing data BACK INTO Anaplan.
    4. Lets you check the "task" status and download the final,
       stored forecast output - so you can prove round-trip worked.

Run it with:
    uvicorn mock_anaplan_server:app --reload --port 8000

Then open http://127.0.0.1:8000/docs in your browser to see and try
every endpoint (FastAPI gives you this Swagger UI for free).
------------------------------------------------------------
"""

import io
import uuid
import random
import datetime as dt

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

app = FastAPI(
    title="Mock Anaplan API",
    description="A tiny local stand-in for the real Anaplan REST API, used for building/testing integrations.",
    version="1.0",
)

# ============================================================
# 1. FAKE "DATABASE" (all in memory - resets when you restart the server)
# ============================================================

WORKSPACE_ID = "wrk-001"
MODEL_ID = "mod-101"
INPUT_FILE_ID = "file-201"          # the file Anaplan "exports" (input data)
OUTPUT_FILE_ID = "file-202"         # the file we "import" (forecast output)
IMPORT_PROCESS_ID = "proc-301"

VALID_TOKENS = set()                # tokens handed out after login
UPLOADED_CHUNKS = {}                 # chunkId -> raw text uploaded by client
TASKS = {}                            # taskId -> task dict
STORED_FORECAST_OUTPUT = {"csv": None, "pushed_at": None}


def make_token() -> str:
    return f"mock-oauth-token-{uuid.uuid4().hex[:12]}"


def require_auth(authorization: str | None):
    """Very small helper: any endpoint that needs a login calls this."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token. Call /oauth2/token first.")
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


# ============================================================
# 2. SYNTHETIC "INPUT DATA" GENERATOR
#    (mimics the "Input data to model" tab in the screenshot)
# ============================================================

REGIONS = ["North East", "Mid West", "South", "West"]
CHANNELS = ["Agency", "Direct", "Broker"]
INDUSTRIES = ["Agriculture", "Manufacturing", "Retail", "Healthcare"]
ACCOUNT_SIZES = ["Small", "Medium", "Large"]


def _generate_history_csv(n_months: int = 24) -> str:
    """
    Builds a synthetic monthly history for a handful of Region/Channel/
    Industry_Class/Account_Size combinations. This stands in for the real
    Anaplan module export shown in the screenshot's left-hand side.
    """
    random.seed(42)
    rows = []
    combos = [
        ("Mid West", "Agency", "Agriculture", "Large"),
        ("North East", "Agency", "Agriculture", "Small"),
        ("South", "Direct", "Manufacturing", "Medium"),
        ("West", "Broker", "Retail", "Small"),
        ("Mid West", "Direct", "Healthcare", "Medium"),
    ]

    start = dt.date(2024, 1, 1)

    for region, channel, industry, size in combos:
        base_wage = random.uniform(35000, 50000)
        base_payroll = random.uniform(50_000_000, 60_000_000)
        wage = base_wage
        payroll = base_payroll
        prev_year_wage = {}

        for m in range(n_months):
            month_date = (start.replace(day=1) + dt.timedelta(days=32 * m)).replace(day=1)

            # small random walk + mild seasonal wiggle for realism
            seasonal = 1 + 0.02 * random.uniform(-1, 1)
            wage = wage * (1 + random.uniform(-0.01, 0.02)) * seasonal
            payroll = payroll * (1 + random.uniform(-0.01, 0.015))
            employees = int(payroll / wage)

            qoq_growth = random.uniform(-0.02, 0.05)
            yoy_growth = random.uniform(0.0, 0.09)

            rows.append({
                "Month": month_date.isoformat(),
                "Region": region,
                "Channel": channel,
                "Industry_Class": industry,
                "Account_Size": size,
                "Payroll": round(payroll, 2),
                "Employee_Count": employees,
                "Avg_Wage": round(wage, 2),
                "Payroll_Growth_Rate_YoY": round(yoy_growth, 4),
                "Payroll_Growth_Rate_QoQ": round(qoq_growth, 4),
                "Hazard_Group": random.choice([1, 2, 3, 4]),
                "Historical_Loss_Ratio": round(random.uniform(0.6, 0.9), 4),
                "Claim_Frequency": round(random.uniform(0.0, 0.05), 4),
                "Claim_Severity": round(random.uniform(20000, 35000), 2),
                "Wage_Inflation_Index": round(1 + random.uniform(0.02, 0.07), 4),
                "Employer_Tenure": round(random.uniform(4.5, 6.0), 3),
                "Retention_Rate": round(random.uniform(0.70, 0.85), 4),
                "Churn_Probability": round(random.uniform(0.15, 0.30), 4),
                "Seasonality_Index": round(random.uniform(-0.5, 0.5), 4),
                "Economic_Indicator": round(random.uniform(0.4, 0.9), 4),
                "Employment_Growth_Rate": round(random.uniform(0.005, 0.02), 4),
            })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


# Generate once at startup, like a real export snapshot.
INPUT_DATA_CSV = _generate_history_csv()


# ============================================================
# 3. AUTH ENDPOINTS
# ============================================================

@app.post("/oauth2/token")
def oauth_token(grant_type: str = "client_credentials",
                 client_id: str = "demo-client",
                 client_secret: str = "demo-secret"):
    """
    Mimics Anaplan's OAuth2 client-credentials login.
    Any client_id/client_secret is accepted for this mock (it's not real security).
    """
    token = make_token()
    VALID_TOKENS.add(token)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@app.post("/api/2/0/basicAuth")
def basic_auth_login():
    """Mimics Anaplan Basic Auth login, for completeness."""
    token = make_token()
    VALID_TOKENS.add(token)
    return {"status": "SUCCESS", "statusMessage": "Login successful", "token": token}


# ============================================================
# 4. WORKSPACE / MODEL DISCOVERY (so client scripts can "browse" like real Anaplan)
# ============================================================

@app.get("/api/2/0/workspaces")
def list_workspaces(authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"workspaces": [{"id": WORKSPACE_ID, "name": "Forecasting Workspace", "active": True}]}


@app.get("/api/2/0/workspaces/{workspace_id}/models")
def list_models(workspace_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"models": [{"id": MODEL_ID, "name": "Workers Comp Wage Forecast Model",
                         "currentWorkspaceId": workspace_id, "isActive": True}]}


@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files")
def list_files(workspace_id: str, model_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"files": [
        {"id": INPUT_FILE_ID, "name": "Input_Data.csv", "hasHeader": True},
        {"id": OUTPUT_FILE_ID, "name": "Forecast_Output.csv", "hasHeader": True},
    ]}


# ============================================================
# 5. EXPORT: download the INPUT data (Anaplan -> downstream system)
# ============================================================

@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}")
def download_file(workspace_id: str, model_id: str, file_id: str,
                   authorization: str | None = Header(default=None)):
    """
    Downloads a file. In real Anaplan this returns the file bytes for the
    given fileId. Here:
      - file-201 (Input_Data.csv)   -> the synthetic historical input data
      - file-202 (Forecast_Output.csv) -> whatever forecast we last pushed in
    """
    require_auth(authorization)

    if file_id == INPUT_FILE_ID:
        return PlainTextResponse(content=INPUT_DATA_CSV, media_type="text/csv")

    if file_id == OUTPUT_FILE_ID:
        if STORED_FORECAST_OUTPUT["csv"] is None:
            raise HTTPException(status_code=404, detail="No forecast output has been pushed yet.")
        return PlainTextResponse(content=STORED_FORECAST_OUTPUT["csv"], media_type="text/csv")

    raise HTTPException(status_code=404, detail=f"Unknown file id: {file_id}")


# ============================================================
# 6. IMPORT: upload a chunk containing the FORECAST output
#    (downstream system -> Anaplan)
# ============================================================

@app.put("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/chunks/{chunk_id}")
async def upload_chunk(workspace_id: str, model_id: str, file_id: str, chunk_id: str,
                        request: Request, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    if file_id != OUTPUT_FILE_ID:
        raise HTTPException(status_code=404, detail=f"Unknown file id for upload: {file_id}")

    body = await request.body()
    UPLOADED_CHUNKS[chunk_id] = body.decode("utf-8")
    return {"status": "SUCCESS", "statusMessage": f"Chunk {chunk_id} uploaded successfully"}


# ============================================================
# 7. RUN IMPORT PROCESS (takes the uploaded chunk(s) and "loads" them into the model)
# ============================================================

@app.post("/api/2/0/workspaces/{workspace_id}/models/{model_id}/processes/{process_id}/tasks")
def run_process(workspace_id: str, model_id: str, process_id: str,
                 authorization: str | None = Header(default=None)):
    require_auth(authorization)
    if process_id != IMPORT_PROCESS_ID:
        raise HTTPException(status_code=404, detail=f"Unknown process id: {process_id}")

    # Assemble all uploaded chunks (in this simple mock we just use chunk "0")
    csv_text = UPLOADED_CHUNKS.get("0")
    if csv_text is None:
        raise HTTPException(status_code=400, detail="No uploaded data found. Upload a chunk before running the process.")

    # "Load" it into the model
    STORED_FORECAST_OUTPUT["csv"] = csv_text
    STORED_FORECAST_OUTPUT["pushed_at"] = dt.datetime.utcnow().isoformat() + "Z"

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    TASKS[task_id] = {
        "taskId": task_id,
        "status": "COMPLETE",   # instantly complete for simplicity of this mock
        "result": {"successful": True, "failureDumpAvailable": False, "objectId": process_id},
        "progress": 100,
        "createdTime": dt.datetime.utcnow().isoformat() + "Z",
    }
    return {"taskId": task_id, "status": "COMPLETE"}


@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/tasks/{task_id}")
def get_task(workspace_id: str, model_id: str, task_id: str,
             authorization: str | None = Header(default=None)):
    require_auth(authorization)
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Unknown task id: {task_id}")
    return task


# ============================================================
# 8. HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Mock Anaplan server is running.",
        "docs": "Open /docs in your browser for interactive API docs.",
        "workspace_id": WORKSPACE_ID,
        "model_id": MODEL_ID,
        "input_file_id": INPUT_FILE_ID,
        "output_file_id": OUTPUT_FILE_ID,
        "import_process_id": IMPORT_PROCESS_ID,
    }
