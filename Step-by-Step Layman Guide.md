# 🚀 End-to-End Layman Guide: FastAPI Mock Anaplan & Streamlit Integration

This guide walks you through setting up, running, and testing the entire data flow in **VS Code** and **Postman** without requiring prior backend experience.

---

## 🏗️ Architecture & Data Flow Overview

```
[ POSTMAN ] ─── Uploads Data / Triggers ───┐
                                           ▼
                                [ Mock Anaplan API (FastAPI) ]
                                  Port: 8000
                                  │          ▲
            1. Pulls Input Data   │          │ 3. Pushes Forecast Results
                                  ▼          │
                                [ Streamlit App (ML Engine) ]
                                  Port: 8501
                                  └─ Runs Forecast Model & Dashboard
```

1. **Mock Anaplan Server (`mock_anaplan_server.py`)**: Stores raw data and accepts completed forecasts.
2. **Streamlit App (`app.py`)**: Pulls data from Anaplan, trains an ML model, plots predictions, and pushes data back.
3. **Postman**: Used to upload new inputs into Anaplan or verify that the forecast arrived safely.

---

## 🛠️ Step 1: Open and Setup in VS Code

1. Open your project folder in **VS Code**.
2. Open the built-in terminal in VS Code (`Ctrl + \`` or `Cmd + \`` or menu: **Terminal -> New Terminal**).
3. (Optional but recommended) Create and activate a Python virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate on Windows (Command Prompt / PowerShell)
   .\venv\Scripts\activate

   # Activate on Mac / Linux
   source venv/bin/activate
   ```
4. Install all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🏃 Step 2: Run the Mock Anaplan Server in VS Code

1. In your first VS Code Terminal tab, start the FastAPI server:
   ```bash
   python mock_anaplan_server.py
   ```
2. You will see an output like:
   ```
   INFO:     Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000) (Press CTRL+C to quit)
   ```
3. **Verify in Browser**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). You will see interactive Swagger documentation listing all Anaplan API endpoints.

---

## 📊 Step 3: Run the Streamlit App in VS Code

1. Open a **second terminal tab** in VS Code (click the `+` button in the Terminal panel).
2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
3. Your browser will automatically open [http://localhost:8501](http://localhost:8501).
4. You will see:
   - 🟢 **Mock Anaplan Server: CONNECTED**
   - Click **"🔄 Sync with Anaplan"** -> It fetches data from FastAPI.
   - The ML model automatically calculates the forecast horizon.
   - Click **"🚀 Push Forecast Output to Anaplan"** -> Balloons will appear, confirming data is sent back to the server!

---

## 📮 Step 4: Step-by-Step Testing with Postman (Layman Guide)

Open Postman on your computer. Follow these 4 simple requests:

---

### Request A: Check Anaplan Server Status
* **Purpose**: Check if Anaplan is healthy.
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/`
* **Steps**:
  1. Set the dropdown to `GET`.
  2. Paste `http://127.0.0.1:8000/`.
  3. Click **Send**.
* **Expected Response (`200 OK`)**:
  ```json
  {
    "status": "ONLINE",
    "service": "Mock Anaplan API Server",
    "raw_data_rows": 12,
    "stored_forecast_rows": 0,
    "last_updated": "Default Seed Data"
  }
  ```

---

### Request B: Upload a New Dataset to Anaplan (JSON Mode)
* **Purpose**: Simulates updating Anaplan's source records with new historical data.
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/anaplan/data/upload-json`
* **Headers**: `Content-Type: application/json`
* **Body** -> Select `raw` -> Select `JSON`:
  ```json
  {
    "records": [
      {"Date": "2025-01-01", "Region": "Europe", "Product": "Monitors", "Demand": 500, "Price": 300},
      {"Date": "2025-02-01", "Region": "Europe", "Product": "Monitors", "Demand": 550, "Price": 295},
      {"Date": "2025-03-01", "Region": "Europe", "Product": "Monitors", "Demand": 610, "Price": 290},
      {"Date": "2025-04-01", "Region": "Europe", "Product": "Monitors", "Demand": 680, "Price": 290},
      {"Date": "2025-05-01", "Region": "Europe", "Product": "Monitors", "Demand": 720, "Price": 285}
    ]
  }
  ```
* Click **Send**.
* **What happens next**: Go to your Streamlit app in the browser, click **"🔄 Sync with Anaplan"**, and notice the chart and predictions update instantly for Europe Monitors!

---

### Request C: Upload an `input.csv` File to Anaplan (CSV Mode)
* **Purpose**: Upload a real `.csv` file into Anaplan without typing JSON manually.
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/anaplan/data/upload-csv`
* **Body**:
  1. Select **`form-data`**.
  2. Under **KEY**, type `file` and change the dropdown from *Text* to **File**.
  3. Under **VALUE**, browse and select your `input.csv`.
* Click **Send**.

---

### Request D: Verify the Streamlit Forecast in Anaplan
* **Purpose**: Check the forecast data that Streamlit pushed into Anaplan.
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/anaplan/import/forecast`
* Click **Send**.
* **Expected Response (`200 OK`)**:
  ```json
  {
    "status": "SUCCESS",
    "target_module": "Demand_Forecast_Output_Module",
    "total_records": 18,
    "last_updated": "Forecast updated by ML Model (Linear Trend + Seasonality) at 2026-08-31 18:20:00",
    "forecast_data": [
      {
        "Date": "2025-01-01",
        "Region": "North America",
        "Product": "Laptops",
        "Actual_or_Forecast": "Historical Actual",
        "Predicted_Demand": 120.0
      },
      {
        "Date": "2026-01-01",
        "Region": "North America",
        "Product": "Laptops",
        "Actual_or_Forecast": "ML Forecast",
        "Predicted_Demand": 325.4
      }
    ]
  }
  ```

---

## 🎯 Summary of How This Solves Your Problem

| Old Manual Workflow | New Automated Anaplan Workflow |
|---|---|
| 1. Open Streamlit and upload `input.csv` manually. | 1. Postman/Anaplan automatically serves raw data via `GET /api/v1/anaplan/export/data`. |
| 2. Manually adjust parameters. | 2. Streamlit auto-syncs from Anaplan on load. |
| 3. Manually click download `output.csv`. | 3. One-click **"🚀 Push Forecast Output to Anaplan"** writes directly into Anaplan. |
| 4. Manually upload `output.csv` into Anaplan. | 4. Anaplan Target module is instantly updated via API (`POST /api/v1/anaplan/import/forecast`). |