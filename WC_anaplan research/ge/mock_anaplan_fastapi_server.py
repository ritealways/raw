import os
import sys
import subprocess
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

app = FastAPI(
    title="Mock Anaplan REST API Server",
    description="Simulates Anaplan API v2.0 for input/output Excel files and LightGBM model execution.",
    version="2.0.0"
)

# Standard mock authorization token
MOCK_TOKEN = "Bearer mock-anaplan-auth-token-9999"

# Workspace and file definitions
INPUT_FILE_NAME = "input_excel.xlsx"
OUTPUT_FILE_NAME = "Output_excel.xlsx"

@app.post("/api/2/0/auth/authenticate")
async def authenticate():
    """
    Simulates Anaplan authentication endpoint.
    Returns a mock Bearer authorization token.
    """
    return {
        "status": "SUCCESS",
        "tokenInfo": {
            "tokenValue": MOCK_TOKEN,
            "expiresIn": 3600
        }
    }

@app.post("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/upload")
async def upload_input_file(
    workspace_id: str,
    model_id: str,
    file_id: str,
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """
    Simulates uploading an input file into Anaplan.
    Saves the incoming Excel file as 'input_excel.xlsx'.
    """
    if authorization != MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing authorization token."
        )

    try:
        # Save file directly to root directory as input_excel.xlsx
        contents = await file.read()
        with open(INPUT_FILE_NAME, "wb") as f:
            f.write(contents)
        
        return {
            "status": "SUCCESS",
            "message": f"File '{file.filename}' successfully uploaded to Mock Anaplan as '{INPUT_FILE_NAME}'.",
            "workspaceId": workspace_id,
            "modelId": model_id,
            "fileId": file_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@app.post("/api/2/0/workspaces/{workspace_id}/models/{model_id}/processes/{process_id}/tasks")
async def execute_process(
    workspace_id: str,
    model_id: str,
    process_id: str,
    authorization: str = Header(None)
):
    """
    Triggers the forecasting process pipeline.py (which runs wc_lgbm.py).
    """
    if authorization != MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing authorization token."
        )

    # Check if input file exists
    if not os.path.exists(INPUT_FILE_NAME):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Required file '{INPUT_FILE_NAME}' not found. Please upload it first via Step 2."
        )

    try:
        # Run pipeline.py using current python environment
        result = subprocess.run(
            [sys.executable, "pipeline.py"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "taskId": "task-proc-forecast-error",
                    "status": "FAILED",
                    "result": {
                        "successful": False,
                        "errorDetails": result.stderr or result.stdout
                    }
                }
            )

        return {
            "taskId": "task-proc-forecast-001",
            "status": "COMPLETE",
            "result": {
                "successful": True,
                "message": "Pipeline completed successfully. Output excel generated.",
                "logs": result.stdout.strip()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution error: {str(e)}"
        )

@app.get("/api/2/0/workspaces/{workspace_id}/models/{model_id}/files/{file_id}/download")
async def download_output_file(
    workspace_id: str,
    model_id: str,
    file_id: str,
    authorization: str = Header(None)
):
    """
    Simulates downloading the generated forecast output file ('Output_excel.xlsx') back to Anaplan.
    """
    if authorization != MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing authorization token."
        )

    if not os.path.exists(OUTPUT_FILE_NAME):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output file '{OUTPUT_FILE_NAME}' does not exist. Run the process task first."
        )

    return FileResponse(
        path=OUTPUT_FILE_NAME,
        filename=OUTPUT_FILE_NAME,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    print("Starting Mock Anaplan REST API Server on http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)