"""
Mock Anaplan Server
-------------------
This FastAPI server simulates Anaplan's REST APIs:
1. Export API: Serves raw historical input data to downstream consumers (Streamlit).
2. Upload API: Allows uploading new datasets into Anaplan via Postman.
3. Import API: Receives generated forecast outputs from ML applications.
4. Audit API: Allows checking the current state and stored forecasts.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import uvicorn

app = FastAPI(
    title="Mock Anaplan Enterprise REST API",
    description="Simulates Anaplan Export, Import, and Model Data Transfer endpoints.",
    version="1.0.0"
)

# Enable CORS for local cross-app communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# IN-MEMORY DATA STORE (Simulating Anaplan Modules / Data Hub)
# ==============================================================================

# Default historical time-series data
DEFAULT_RAW_DATA = [
    {"Date": "2025-01-01", "Region": "North America", "Product": "Laptops", "Demand": 120, "Price": 950},
    {"Date": "2025-02-01", "Region": "North America", "Product": "Laptops", "Demand": 135, "Price": 940},
    {"Date": "2025-03-01", "Region": "North America", "Product": "Laptops", "Demand": 150, "Price": 930},
    {"Date": "2025-04-01", "Region": "North America", "Product": "Laptops", "Demand": 160, "Price": 920},
    {"Date": "2025-05-01", "Region": "North America", "Product": "Laptops", "Demand": 175, "Price": 920},
    {"Date": "2025-06-01", "Region": "North America", "Product": "Laptops", "Demand": 190, "Price": 910},
    {"Date": "2025-07-01", "Region": "North America", "Product": "Laptops", "Demand": 210, "Price": 900},
    {"Date": "2025-08-01", "Region": "North America", "Product": "Laptops", "Demand": 205, "Price": 900},
    {"Date": "2025-09-01", "Region": "North America", "Product": "Laptops", "Demand": 225, "Price": 890},
    {"Date": "2025-10-01", "Region": "North America", "Product": "Laptops", "Demand": 240, "Price": 890},
    {"Date": "2025-11-01", "Region": "North America", "Product": "Laptops", "Demand": 280, "Price": 880},
    {"Date": "2025-12-01", "Region": "North America", "Product": "Laptops", "Demand": 310, "Price": 870}
]

# State storage
anaplan_database = {
    "source_dataset": DEFAULT_RAW_DATA,
    "forecast_module": [],
    "last_updated": "Default Seed Data"
}

# ==============================================================================
# DATA MODELS
# ==============================================================================

class DataRecord(BaseModel):
    Date: str
    Region: Optional[str] = "Default"
    Product: Optional[str] = "Default"
    Demand: float
    Price: Optional[float] = 0.0

class DatasetPayload(BaseModel):
    records: List[Dict[str, Any]]

class ForecastRecord(BaseModel):
    Date: str
    Region: Optional[str] = "All"
    Product: Optional[str] = "All"
    Actual_or_Forecast: str
    Predicted_Demand: float

class ForecastPayload(BaseModel):
    model_name: str
    timestamp: str
    forecast_records: List[Dict[str, Any]]

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/", tags=["Health"])
def health_check():
    """Health check and overview of current Anaplan data state."""
    return {
        "status": "ONLINE",
        "service": "Mock Anaplan API Server",
        "raw_data_rows": len(anaplan_database["source_dataset"]),
        "stored_forecast_rows": len(anaplan_database["forecast_module"]),
        "last_updated": anaplan_database["last_updated"]
    }

# ------------------------------------------------------------------------------
# 1. ANAPLAN EXPORT (Streamlit pulls data from here)
# ------------------------------------------------------------------------------
@app.get("/api/v1/anaplan/export/data", tags=["Anaplan Export"])
def export_raw_data():
    """
    Simulates: Anaplan Export Action
    Allows downstream applications (Streamlit) to fetch raw input data.
    """
    if not anaplan_database["source_dataset"]:
        raise HTTPException(status_code=404, detail="No source data available in Anaplan.")
    
    return {
        "status": "SUCCESS",
        "module": "Demand_Planning_Input",
        "total_records": len(anaplan_database["source_dataset"]),
        "data": anaplan_database["source_dataset"]
    }

# ------------------------------------------------------------------------------
# 2. ANAPLAN DATA INGESTION (Postman uploads raw data here)
# ------------------------------------------------------------------------------
@app.post("/api/v1/anaplan/data/upload-json", tags=["Anaplan Source Ingestion"])
def upload_data_json(payload: DatasetPayload):
    """
    Allows Postman or data pipelines to push raw JSON data into Anaplan.
    """
    if not payload.records:
        raise HTTPException(status_code=400, detail="Payload records cannot be empty.")
    
    anaplan_database["source_dataset"] = payload.records
    anaplan_database["last_updated"] = "Updated via Postman (JSON)"
    
    return {
        "status": "SUCCESS",
        "message": f"Successfully loaded {len(payload.records)} records into Anaplan source module.",
        "records_loaded": len(payload.records)
    }

@app.post("/api/v1/anaplan/data/upload-csv", tags=["Anaplan Source Ingestion"])
async def upload_data_csv(file: UploadFile = File(...)):
    """
    Allows Postman to upload an input.csv file directly into the mock Anaplan server.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .csv file.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        records = df.to_dict(orient="records")
        anaplan_database["source_dataset"] = records
        anaplan_database["last_updated"] = f"Updated via CSV Upload ({file.filename})"
        
        return {
            "status": "SUCCESS",
            "message": f"Successfully parsed and loaded {len(records)} rows from {file.filename}.",
            "columns": list(df.columns),
            "sample_row": records[0] if records else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse CSV: {str(e)}")

# ------------------------------------------------------------------------------
# 3. ANAPLAN IMPORT (Streamlit pushes forecast output here)
# ------------------------------------------------------------------------------
@app.post("/api/v1/anaplan/import/forecast", tags=["Anaplan Import"])
def import_forecast_output(payload: ForecastPayload):
    """
    Simulates: Anaplan Import Action / Data Hub writeback
    Receives forecasting output pushed from the Streamlit ML pipeline.
    """
    if not payload.forecast_records:
        raise HTTPException(status_code=400, detail="No forecast records provided.")
    
    anaplan_database["forecast_module"] = payload.forecast_records
    anaplan_database["last_updated"] = f"Forecast updated by ML Model ({payload.model_name}) at {payload.timestamp}"
    
    return {
        "status": "SUCCESS",
        "message": "Forecast output successfully imported into Anaplan Target Line Items.",
        "model_name": payload.model_name,
        "records_written": len(payload.forecast_records),
        "imported_at": payload.timestamp
    }

# ------------------------------------------------------------------------------
# 4. VIEW STORED FORECAST (Inspect results via Postman / Browser)
# ------------------------------------------------------------------------------
@app.get("/api/v1/anaplan/import/forecast", tags=["Anaplan Import"])
def view_stored_forecast():
    """
    Inspect the forecast currently stored inside Anaplan (verify postback from Streamlit).
    """
    return {
        "status": "SUCCESS",
        "target_module": "Demand_Forecast_Output_Module",
        "total_records": len(anaplan_database["forecast_module"]),
        "last_updated": anaplan_database["last_updated"],
        "forecast_data": anaplan_database["forecast_module"]
    }

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
if __name__ == "__main__":
    # Runs the server locally on http://127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)