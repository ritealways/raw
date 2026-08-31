"""
MOCK ANAPLAN SERVER
--------------------
This is a small FastAPI app that PRETENDS to be Anaplan.

Why do we need this?
Anaplan is normally a cloud system. Since you don't have a real Anaplan
connection to test with, this script acts as a stand-in "fake Anaplan"
running on your own laptop, so you can test the full flow:

    Anaplan (mock) --> Streamlit app --> Anaplan (mock)

It stores files on your disk in a folder called "anaplan_storage".

ENDPOINTS (think of these as "doors" Postman or Streamlit can knock on):

1. GET  /                      -> health check, confirms server is alive
2. POST /anaplan/input         -> (Postman) upload input.csv INTO "Anaplan"
3. GET  /anaplan/input         -> (Streamlit) download input.csv FROM "Anaplan"
4. POST /anaplan/output        -> (Streamlit) upload output.csv INTO "Anaplan"
5. GET  /anaplan/output        -> (Postman) download output.csv FROM "Anaplan"
   to prove the push worked
6. GET  /anaplan/status        -> shows what files currently exist
"""

import os
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="Mock Anaplan Server")

# Folder where the "fake Anaplan" keeps its files
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "anaplan_storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

INPUT_PATH = os.path.join(STORAGE_DIR, "input.csv")
OUTPUT_PATH = os.path.join(STORAGE_DIR, "output.csv")


@app.get("/")
def health_check():
    return {"status": "Mock Anaplan server is running"}


@app.post("/anaplan/input")
async def upload_input(file: UploadFile = File(...)):
    """
    Use this from POSTMAN to load input.csv INTO the mock Anaplan,
    simulating that Anaplan already has data ready for the model.
    """
    contents = await file.read()
    with open(INPUT_PATH, "wb") as f:
        f.write(contents)
    return {
        "message": "input.csv received and stored in mock Anaplan",
        "size_bytes": len(contents),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/anaplan/input")
def download_input():
    """
    Use this from STREAMLIT (app.py) to pull the input data FROM Anaplan
    before running the model.
    """
    if not os.path.exists(INPUT_PATH):
        raise HTTPException(status_code=404, detail="No input.csv found in mock Anaplan yet. Upload it first via Postman.")
    return FileResponse(INPUT_PATH, media_type="text/csv", filename="input.csv")


@app.post("/anaplan/output")
async def upload_output(file: UploadFile = File(...)):
    """
    Use this from STREAMLIT (app.py) to push the forecasting results
    (output.csv) back INTO Anaplan after the model finishes running.
    """
    contents = await file.read()
    with open(OUTPUT_PATH, "wb") as f:
        f.write(contents)
    return {
        "message": "output.csv received and stored in mock Anaplan",
        "size_bytes": len(contents),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/anaplan/output")
def download_output():
    """
    Use this from POSTMAN to confirm the forecast output really landed
    in Anaplan, and to download it for inspection.
    """
    if not os.path.exists(OUTPUT_PATH):
        raise HTTPException(status_code=404, detail="No output.csv found yet. Run the Streamlit app first.")
    return FileResponse(OUTPUT_PATH, media_type="text/csv", filename="output.csv")


@app.get("/anaplan/status")
def status():
    return JSONResponse({
        "input_available": os.path.exists(INPUT_PATH),
        "output_available": os.path.exists(OUTPUT_PATH),
        "storage_folder": STORAGE_DIR,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("anaplan_mock_server:app", host="127.0.0.1", port=8000, reload=True)
