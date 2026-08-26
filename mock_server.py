r"""
mock_server.py
------------------------------------------------------------
A SIMPLE MOCK ANAPLAN SERVER (built with FastAPI).

WHAT THIS DOES (in plain English):
    It pretends to be Anaplan on your own computer so you can build/test
    an integration without a real Anaplan tenant.

    - When something asks to "export" data, it reads YOUR real
      input_excel.xlsx file from disk and sends it out.
    - When something "imports"/pushes data back, it saves whatever it
      receives as YOUR real Output_excel.xlsx file on disk.

    IMPORTANT: This does NOT invent or generate any fake data. It only
    reads/writes the two Excel files you point it at below. If
    input_excel.xlsx doesn't exist yet at the configured path, the
    export endpoint will simply return a "file not found" error telling
    you to put your file there.

------------------------------------------------------------
============  >>>  EDIT THESE TWO LINES  <<<  ================
------------------------------------------------------------
Set these to the actual location of your two Excel files on YOUR
computer. You can use a relative path (if the file sits in the same
folder as this script) or a full path.

Examples (Windows):
    INPUT_EXCEL_PATH  = r"C:\Users\yourname\Documents\input_excel.xlsx"
    OUTPUT_EXCEL_PATH = r"C:\Users\yourname\Documents\Output_excel.xlsx"

Examples (Mac/Linux):
    INPUT_EXCEL_PATH  = "/Users/yourname/Documents/input_excel.xlsx"
    OUTPUT_EXCEL_PATH = "/Users/yourname/Documents/Output_excel.xlsx"
------------------------------------------------------------
"""

INPUT_EXCEL_PATH = "./data/input_excel.xlsx"
OUTPUT_EXCEL_PATH = "./data/Output_excel.xlsx"

# ------------------------------------------------------------
# You normally don't need to touch anything below this line.
# ------------------------------------------------------------

import os
import uuid
import datetime as dt
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse

app = FastAPI(
    title="Mock Anaplan API",
    description="Local stand-in for the real Anaplan REST API. Serves your real input_excel.xlsx and stores whatever is pushed back as Output_excel.xlsx.",
    version="1.0",
)

# ============================================================
# FAKE IDS (stand-ins for real Anaplan workspace/model/file/process IDs)
# ============================================================
WORKSPACE_ID = "wrk-001"
MODEL_ID = "mod-101"
INPUT_FILE_ID = "file-201"          # represents input_excel.xlsx
OUTPUT_FILE_ID = "file-202"         # represents Output_excel.xlsx
IMPORT_PROCESS_ID = "proc-301"

VALID_TOKENS = set()
UPLOADED_CHUNKS = {}   # chunkId -> raw bytes received from the client
TASKS = {}             # taskId -> task status dict


def make_token() -> str:
    return f"mock-oauth-token-{uuid.uuid4().hex[:12]}"


def require_auth(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token. Call /oauth2/token first.")
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


# ============================================================
# AUTH
# ============================================================
@app.post("/oauth2/token")
def oauth_token():
    """Mimics Anaplan's OAuth2 login. Any call succeeds (this is a local mock, not real security)."""
    token = make_token()
    VALID_TOKENS.add(token)
    return {"access_token": token, "token_type": "Bearer", "expires_in": 3600}


# ============================================================
# WORKSPACE / MODEL / FILE DISCOVERY
# ============================================================
@app.get("/api/2/0/workspaces")
def list_workspaces(authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"workspaces": [{"id": WORKSPACE_ID, "name": "Forecasting Workspace", "active": True}]}


@app.get("/api/2/0/workspaces/{workspace_id}/models")
def list_models(workspace_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"models": [{"id": MODEL_ID, "name": "Wage Forecast Model", "isActive": True}]}


@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files")
def list_files(workspace_id: str, model_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"files": [
        {"id": INPUT_FILE_ID, "name": os.path.basename(INPUT_EXCEL_PATH)},
        {"id": OUTPUT_FILE_ID, "name": os.path.basename(OUTPUT_EXCEL_PATH)},
    ]}


# ============================================================
# EXPORT: download the INPUT excel (Anaplan -> your pipeline)
# ============================================================
@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}")
def download_file(workspace_id: str, model_id: str, file_id: str,
                   authorization: str | None = Header(default=None)):
    require_auth(authorization)

    if file_id == INPUT_FILE_ID:
        if not Path(INPUT_EXCEL_PATH).exists():
            raise HTTPException(
                status_code=404,
                detail=(f"input_excel not found at '{INPUT_EXCEL_PATH}'. "
                        f"Edit INPUT_EXCEL_PATH at the top of mock_server.py to point "
                        f"at your real file, or place your file at that path.")
            )
        return FileResponse(
            path=INPUT_EXCEL_PATH,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(INPUT_EXCEL_PATH),
        )

    if file_id == OUTPUT_FILE_ID:
        if not Path(OUTPUT_EXCEL_PATH).exists():
            raise HTTPException(status_code=404, detail="No forecast output has been pushed yet.")
        return FileResponse(
            path=OUTPUT_EXCEL_PATH,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(OUTPUT_EXCEL_PATH),
        )

    raise HTTPException(status_code=404, detail=f"Unknown file id: {file_id}")


# ============================================================
# IMPORT: upload the OUTPUT excel (your pipeline -> Anaplan)
# ============================================================
@app.put("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/chunks/{chunk_id}")
async def upload_chunk(workspace_id: str, model_id: str, file_id: str, chunk_id: str,
                        request: Request, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    if file_id != OUTPUT_FILE_ID:
        raise HTTPException(status_code=404, detail=f"Unknown file id for upload: {file_id}")

    body = await request.body()
    UPLOADED_CHUNKS[chunk_id] = body  # raw excel bytes
    return {"status": "SUCCESS", "statusMessage": f"Chunk {chunk_id} uploaded successfully ({len(body)} bytes)"}


@app.post("/api/2/0/workspaces/{workspace_id}/models/{model_id}/processes/{process_id}/tasks")
def run_process(workspace_id: str, model_id: str, process_id: str,
                 authorization: str | None = Header(default=None)):
    require_auth(authorization)
    if process_id != IMPORT_PROCESS_ID:
        raise HTTPException(status_code=404, detail=f"Unknown process id: {process_id}")

    raw_bytes = UPLOADED_CHUNKS.get("0")
    if raw_bytes is None:
        raise HTTPException(status_code=400, detail="No uploaded data found. Upload a chunk before running the process.")

    # "Load" it: write it to disk as the real Output_excel.xlsx file
    Path(OUTPUT_EXCEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_EXCEL_PATH, "wb") as f:
        f.write(raw_bytes)

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    TASKS[task_id] = {
        "taskId": task_id,
        "status": "COMPLETE",
        "result": {"successful": True, "objectId": process_id},
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
# HEALTH CHECK
# ============================================================
@app.get("/")
def root():
    return {
        "message": "Mock Anaplan server is running.",
        "docs": "Open /docs in your browser for interactive API docs.",
        "input_excel_path": INPUT_EXCEL_PATH,
        "input_excel_found": Path(INPUT_EXCEL_PATH).exists(),
        "output_excel_path": OUTPUT_EXCEL_PATH,
        "workspace_id": WORKSPACE_ID,
        "model_id": MODEL_ID,
        "input_file_id": INPUT_FILE_ID,
        "output_file_id": OUTPUT_FILE_ID,
        "import_process_id": IMPORT_PROCESS_ID,
    }
