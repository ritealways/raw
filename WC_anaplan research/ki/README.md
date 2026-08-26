# 🏗️ Mock Anaplan Server + WC LightGBM Forecasting Pipeline

A complete mock Anaplan REST API server that integrates with a Workers Compensation LightGBM forecasting model. This simulates the real Anaplan → Python Model → Anaplan data flow using Postman or VS Code.

---

## 📁 Project Structure

```
anaplan_mock_server/
│
├── server.py                    # 🚀 Mock Anaplan Flask Server (Main API)
├── test_client.py              # 🧪 VS Code Test Client (Python script)
├── standalone_forecast.py      # 📊 Run forecast without server
├── requirements.txt            # 📦 Python dependencies
├── .gitignore                  # 🚫 Git ignore file
│
├── models/
│   └── wc_lightgbm.py          # 🤖 WC LightGBM Forecasting Model
│
└── README.md                   # 📖 This file
```

---

## 🎯 What This Does

```
┌─────────────────┐     POST /upload-input      ┌──────────────────┐
│   POSTMAN or    │ ───────────────────────────→ │  Mock Anaplan    │
│   VS Code       │                             │    Server        │
│   (Client)      │ ←────────────────────────── │  (Flask API)     │
└─────────────────┘     JSON Response           └──────────────────┘
                                                        │
                                                        │ calls
                                                        ▼
                                              ┌──────────────────┐
                                              │  wc_lightgbm.py  │
                                              │  (Forecast Model)│
                                              └──────────────────┘
                                                        │
                                                        │ returns
                                                        ▼
                                              ┌──────────────────┐
                                              │  P10 / P50 / P90 │
                                              │  Forecast Output │
                                              └──────────────────┘
                                                        │
┌─────────────────┐     POST /push-output       ←──────┘
│   POSTMAN or    │ ←──────────────────────────
│   VS Code       │      "Pushed to Anaplan"
│   (Client)      │
└─────────────────┘
```

**Input** (from your image → left side): 3 months of historical WC data (Payroll, Employee Count, Loss Ratios, etc.)

**Output** (from your image → right side): 3-month forecast with P10, P50 (Median), P90 percentiles

---

## 🛠️ STEP 1: Install Dependencies

### Option A: Using VS Code Terminal

1. **Open VS Code** and open the `anaplan_mock_server` folder
2. **Open Terminal** in VS Code: `Ctrl + ~` (or Terminal → New Terminal)
3. **Create a virtual environment** (recommended):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

4. **Install dependencies**:

```bash
pip install -r requirements.txt
```

> 💡 **What this installs**: Flask (web server), LightGBM (ML model), Pandas/NumPy (data processing), Requests (HTTP client), Scikit-learn (ML utilities)

---

## 🚀 STEP 2: Start the Mock Anaplan Server

### In VS Code Terminal:

```bash
# Make sure you're in the anaplan_mock_server folder
cd anaplan_mock_server

# Start the server
python server.py
```

You should see:
```
======================================================================
  MOCK ANAPLAN SERVER - Workers Compensation Forecasting
======================================================================

  Server starting on: http://localhost:5000

  Available Endpoints:
  - GET  /                    → Server info
  - GET  /api/health          → Health check
  - POST /api/anaplan/upload-input   → Upload input data
  - POST /api/anaplan/run-forecast   → Run wc_lightgbm forecast
  - GET  /api/anaplan/forecast-output→ Get forecast results
  - POST /api/anaplan/push-output    → Push output to Anaplan
  - GET  /api/anaplan/all-data       → View all stored data
  - DELETE /api/anaplan/clear        → Clear all data

======================================================================
 * Running on http://0.0.0.0:5000
```

> ⚠️ **Keep this terminal running!** The server needs to stay active.

---

## 🧪 STEP 3: Test with VS Code (Python Script)

### Open a NEW terminal (don't close the server!)

```bash
# In VS Code: Terminal → New Terminal
# Make sure virtual env is activated, then run:

python test_client.py
```

You'll see a menu:
```
======================================================================
  MOCK ANAPLAN SERVER - VS CODE TEST CLIENT
======================================================================

    Choose an option:

    1. Run FULL Pipeline (Health → Upload → Forecast → Get → Push)
    2. Test Health Check only
    3. Test Upload Input only
    4. Test Run Forecast only
    5. Test Get Forecast only
    6. Test Push Output only
    7. Exit
```

**Type `1` and press Enter** to run the full pipeline.

### Expected Output:
```
======================================================================
  STEP 1: Health Check
======================================================================
✅ Server is healthy and running!

======================================================================
  STEP 2: Upload Input Data to Mock Anaplan
======================================================================
✅ Uploaded 3 records successfully!

======================================================================
  STEP 3: Run wc_lightgbm Forecast Model
======================================================================
✅ Forecast generated successfully!

Forecast Results Table:
--------------------------------------------------------------------------------
Month        Region       Channel    Industry     Size     P10          P50          P90
--------------------------------------------------------------------------------
Apr-2022     North East   Agency     Agriculture  Small    $856,055     $971,752     $1,120,470
May-2022     North East   Agency     Agriculture  Small    $881,737     $1,000,905   $1,154,084
Jun-2022     North East   Agency     Agriculture  Small    $908,189     $1,030,932   $1,188,707
--------------------------------------------------------------------------------

======================================================================
  STEP 4: Get Forecast Output
======================================================================
✅ Retrieved 3 forecast records!

======================================================================
  STEP 5: Push Output to Anaplan Module
======================================================================
✅ Pushed 3 records to 'WC_Forecast_Module'!

======================================================================
  PIPELINE SUMMARY
======================================================================
  Health Check         → PASS
  Upload Input         → PASS
  Run Forecast         → PASS
  Get Forecast         → PASS
  Push Output          → PASS

🎉 All pipeline steps completed successfully!
```

---

## 📮 STEP 4: Test with Postman (Like a Layman)

### 4.1 Install Postman

1. Go to https://www.postman.com/downloads/
2. Download and install Postman for your OS
3. Open Postman

### 4.2 Create a Collection

1. Click **"Collections"** in the left sidebar
2. Click **"+"** (Create New Collection)
3. Name it: `Mock Anaplan WC Forecast`

### 4.3 Add Requests to the Collection

#### 🔵 REQUEST 1: Health Check

1. Click **"Add Request"** in your collection
2. Name it: `1. Health Check`
3. Set:
   - **Method**: `GET`
   - **URL**: `http://localhost:5000/api/health`
4. Click **"Send"**
5. You should see:
   ```json
   {
     "status": "healthy",
     "server": "Mock Anaplan Server",
     "version": "1.0.0"
   }
   ```

---

#### 🔵 REQUEST 2: Upload Input Data

1. Click **"Add Request"**
2. Name it: `2. Upload Input Data`
3. Set:
   - **Method**: `POST`
   - **URL**: `http://localhost:5000/api/anaplan/upload-input`
4. Click **"Body"** tab → Select **"raw"** → Select **"JSON"** from dropdown
5. Paste this JSON (copy from the `test_client.py` file or below):

```json
{
  "data": [
    {
      "Month": "2022-01-01",
      "Region": "North East",
      "Channel": "Agency",
      "Industry_Class": "Agriculture",
      "Account_Size": "Small",
      "Payroll": 54915332.36,
      "Employee_Count": 1434,
      "Avg_Wage": 47941.17,
      "Payroll_Growth_Rate_YoY": 0.0,
      "Payroll_Growth_Rate_QoQ": 0.0,
      "Hazard_Group": 4,
      "Historical_Loss_Ratio": 0.798,
      "Claim_Frequency": 0.0,
      "Claim_Severity": 31605,
      "Loss_Development_Factor": 1.096,
      "Medical_Inflation_Index": 1.055,
      "Wage_Inflation_Index": 1.03,
      "Employer_Tenure": 5.016,
      "Exposure_Volatility_Score": 0.9302,
      "Filed_Rate_Change": 0.042,
      "Net_Rate_Achievement": 0.036,
      "Schedule_Rating_Factor": 0.9747,
      "Deductible_Level": 0,
      "Renewal_Uplift": 0.063,
      "Loss_Sensitive_Indicator": 0,
      "Policy_Limit_Change": 1,
      "Code_Reclassification_Frequ": 0,
      "Multi_Policy_Bundle_Indicator": 0.39,
      "Retention_Rate": 0.771,
      "Churn_Probability": 0.229,
      "New_Business_Hit_Ratio": 0.276,
      "Submission_to_Bind_Ratio": 0.175,
      "Policy_Term_Length": 12,
      "Endorsement_Frequency": 1,
      "Broker_Concentration": 0.046,
      "Seasonality_Index": -0.5,
      "Economic_Indicator": 0.65,
      "Employment_Growth_Rate": 0.12,
      "GWP": 856055.57
    },
    {
      "Month": "2022-02-01",
      "Region": "North East",
      "Channel": "Agency",
      "Industry_Class": "Agriculture",
      "Account_Size": "Small",
      "Payroll": 56315326.01,
      "Employee_Count": 1357,
      "Avg_Wage": 48368.42,
      "Payroll_Growth_Rate_YoY": 0.03,
      "Payroll_Growth_Rate_QoQ": 0.03,
      "Hazard_Group": 4,
      "Historical_Loss_Ratio": 0.841,
      "Claim_Frequency": 0.0,
      "Claim_Severity": 26910,
      "Loss_Development_Factor": 1.0704,
      "Medical_Inflation_Index": 1.0611,
      "Wage_Inflation_Index": 1.0355,
      "Employer_Tenure": 5.1238,
      "Exposure_Volatility_Score": 2.1805,
      "Filed_Rate_Change": 0.041,
      "Net_Rate_Achievement": 0.038,
      "Schedule_Rating_Factor": 1.1174,
      "Deductible_Level": 0,
      "Renewal_Uplift": 0.07,
      "Loss_Sensitive_Indicator": 0,
      "Policy_Limit_Change": 0,
      "Code_Reclassification_Frequ": 0,
      "Multi_Policy_Bundle_Indicator": 0.27,
      "Retention_Rate": 0.786,
      "Churn_Probability": 0.215,
      "New_Business_Hit_Ratio": 0.185,
      "Submission_to_Bind_Ratio": 0.225,
      "Policy_Term_Length": 12,
      "Endorsement_Frequency": 3,
      "Broker_Concentration": 0.011,
      "Seasonality_Index": -0.3464,
      "Economic_Indicator": 0.6298,
      "Employment_Growth_Rate": 0.008,
      "GWP": 971752.92
    },
    {
      "Month": "2022-03-01",
      "Region": "North East",
      "Channel": "Agency",
      "Industry_Class": "Agriculture",
      "Account_Size": "Small",
      "Payroll": 53848555.91,
      "Employee_Count": 1418,
      "Avg_Wage": 43440.05,
      "Payroll_Growth_Rate_YoY": 0.08,
      "Payroll_Growth_Rate_QoQ": 0.02,
      "Hazard_Group": 4,
      "Historical_Loss_Ratio": 0.758,
      "Claim_Frequency": 0.0,
      "Claim_Severity": 27747,
      "Loss_Development_Factor": 1.0593,
      "Medical_Inflation_Index": 1.066,
      "Wage_Inflation_Index": 1.0413,
      "Employer_Tenure": 5.1777,
      "Exposure_Volatility_Score": 1.5353,
      "Filed_Rate_Change": 0.041,
      "Net_Rate_Achievement": 0.04,
      "Schedule_Rating_Factor": 1.0064,
      "Deductible_Level": 0,
      "Renewal_Uplift": 0.079,
      "Loss_Sensitive_Indicator": 0,
      "Policy_Limit_Change": -1,
      "Code_Reclassification_Frequ": 0,
      "Multi_Policy_Bundle_Indicator": 0.22,
      "Retention_Rate": 0.823,
      "Churn_Probability": 0.177,
      "New_Business_Hit_Ratio": 0.05,
      "Submission_to_Bind_Ratio": 0.585,
      "Policy_Term_Length": 12,
      "Endorsement_Frequency": 0,
      "Broker_Concentration": 0.05,
      "Seasonality_Index": -0.1634,
      "Economic_Indicator": 0.6144,
      "Employment_Growth_Rate": 0.015,
      "GWP": 1120470.33
    }
  ]
}
```

6. Click **"Send"**
7. Expected response:
   ```json
   {
     "status": "success",
     "message": "Successfully uploaded 3 records",
     "records_uploaded": 3,
     "import_id": "imp_20260826_143000"
   }
   ```

---

#### 🔵 REQUEST 3: Run Forecast

1. Click **"Add Request"**
2. Name it: `3. Run Forecast`
3. Set:
   - **Method**: `POST`
   - **URL**: `http://localhost:5000/api/anaplan/run-forecast`
4. Click **"Body"** tab → Select **"raw"** → Select **"JSON"**
5. Paste empty JSON: `{}`
   > 💡 This tells the server to use the previously uploaded data
6. Click **"Send"**
7. Expected response (your forecast output matching the image):
   ```json
   {
     "status": "success",
     "forecast": [
       {
         "Month": "Apr-2022",
         "Region": "North East",
         "Channel": "Agency",
         "Industry_Class": "Agriculture",
         "Account_Size": "Small",
         "P10": 856055.57,
         "P50": 971752.92,
         "P90": 1120470.33
       },
       {
         "Month": "May-2022",
         "Region": "North East",
         "Channel": "Agency",
         "Industry_Class": "Agriculture",
         "Account_Size": "Small",
         "P10": 881737.24,
         "P50": 1000905.51,
         "P90": 1154084.44
       },
       {
         "Month": "Jun-2022",
         "Region": "North East",
         "Channel": "Agency",
         "Industry_Class": "Agriculture",
         "Account_Size": "Small",
         "P10": 908189.36,
         "P50": 1030932.68,
         "P90": 1188706.97
       }
     ]
   }
   ```

---

#### 🔵 REQUEST 4: Get Forecast Output

1. Click **"Add Request"**
2. Name it: `4. Get Forecast Output`
3. Set:
   - **Method**: `GET`
   - **URL**: `http://localhost:5000/api/anaplan/forecast-output`
4. Click **"Send"**
5. Expected: Same forecast JSON as above

---

#### 🔵 REQUEST 5: Push Output to Anaplan

1. Click **"Add Request"**
2. Name it: `5. Push Output to Anaplan`
3. Set:
   - **Method**: `POST`
   - **URL**: `http://localhost:5000/api/anaplan/push-output`
4. Click **"Body"** tab → Select **"raw"** → Select **"JSON"**
5. Paste:
   ```json
   {
     "target_module": "WC_Forecast_Module"
   }
   ```
6. Click **"Send"**
7. Expected:
   ```json
   {
     "status": "success",
     "message": "Successfully pushed 3 records to Anaplan module \"WC_Forecast_Module\"",
     "export_id": "exp_20260826_143005",
     "records_pushed": 3
   }
   ```

---

## 📊 STEP 5: Run Standalone Forecast (No Server Needed)

If you just want to test the wc_lightgbm model without the server:

```bash
python standalone_forecast.py
```

This will:
1. Load the 3 months of input data from your image
2. Run the LightGBM forecasting model
3. Print P10 / P50 / P90 forecasts
4. Save results to `forecast_output.json`

---

## 🔧 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'flask'"
**Fix**: You forgot to install dependencies
```bash
pip install -r requirements.txt
```

### ❌ "Connection refused" or "Cannot connect to server"
**Fix**: The server isn't running. In a separate terminal:
```bash
python server.py
```

### ❌ "No input data found"
**Fix**: You need to upload data first (Step 2) before running forecast (Step 3)

### ❌ "Address already in use"
**Fix**: Another program is using port 5000. Kill it:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### ❌ LightGBM installation fails
**Fix**: The code has a fallback to RandomForest if LightGBM isn't available. Or install it:
```bash
# Windows
pip install lightgbm

# Mac (with Homebrew)
brew install libomp
pip install lightgbm

# Linux
pip install lightgbm
```

---

## 📋 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info & available endpoints |
| `/api/health` | GET | Health check |
| `/api/anaplan/upload-input` | POST | Upload historical input data |
| `/api/anaplan/run-forecast` | POST | Run wc_lightgbm model |
| `/api/anaplan/forecast-output` | GET | Retrieve forecast results |
| `/api/anaplan/push-output` | POST | Push results to Anaplan module |
| `/api/anaplan/all-data` | GET | View all stored data (debug) |
| `/api/anaplan/clear` | DELETE | Clear all stored data |
| `/api/anaplan/auth` | POST | Simulate Anaplan auth |

---

## 🔄 Real Anaplan Integration (Future)

When you're ready to connect to REAL Anaplan, you'll need:

1. **Anaplan Authentication**: Basic Auth or Certificate-based
2. **Workspace ID** and **Model ID** from your Anaplan tenant
3. **Module/View IDs** for input/output data
4. Replace `localhost:5000` with `https://api.anaplan.com/2/0/...`

The Postman collection structure and JSON payloads will be very similar!

---

## 📝 Notes

- The wc_lightgbm model uses **LightGBM** if available, otherwise falls back to **RandomForest**
- Forecast generates **3 months** of P10/P50/P90 predictions
- Input data format matches your Excel image exactly
- All monetary values are in USD
- The mock server stores data in memory (lost on restart)

---

Made with ❤️ for Workers Compensation Forecasting
