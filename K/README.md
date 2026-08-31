# 🌐 Mock Anaplan Server + Streamlit Integration

This project creates a **mock Anaplan server** using FastAPI that integrates with your existing Streamlit app (`app.py`) **without modifying it**.

---

## 📁 Files Included

| File | Purpose |
|------|---------|
| `mock_anaplan_server.py` | FastAPI server that simulates Anaplan API |
| `anaplan_bridge.py` | Bridge script to pull/push data between Anaplan ↔ Streamlit |
| `run_anaplan_workflow.py` | Orchestrator that runs the full workflow |
| `sample_input.csv` | Demo data for testing |
| `requirements.txt` | Python dependencies |

---

## 🏗️ Architecture

```
┌─────────────────┐     POST /upload      ┌─────────────────────┐
│   POSTMAN       │ ────────────────────► │  Mock Anaplan       │
│  (Upload CSV)   │                       │  Server (FastAPI)   │
└─────────────────┘                       │  Port: 8000         │
                                          └──────────┬──────────┘
                                                     │
                              GET /download/{job_id} │
                                                     ▼
                                          ┌─────────────────────┐
                                          │  anaplan_bridge.py  │
                                          │  (Pulls CSV data)   │
                                          └──────────┬──────────┘
                                                     │
                              Loads: bridge_data/    │
                              temp_input_from_anaplan.csv
                                                     ▼
                                          ┌─────────────────────┐
                                          │   YOUR app.py         │
                                          │  (Streamlit App)    │
                                          │  NO CHANGES NEEDED  │
                                          └──────────┬──────────┘
                                                     │
                              User downloads output  │
                                                     ▼
                                          ┌─────────────────────┐
                                          │  anaplan_bridge.py  │
                                          │  (Pushes output)    │
                                          └──────────┬──────────┘
                                                     │
                              POST /output/{job_id}  │
                                                     ▼
                                          ┌─────────────────────┐
                                          │  Mock Anaplan       │
                                          │  Server             │
                                          └─────────────────────┘
```

---

## 🚀 END-TO-END SETUP (Step-by-Step for Beginners)

### Step 0: Prerequisites
- ✅ VS Code installed
- ✅ Python 3.8+ installed
- ✅ Your `app.py` Streamlit app ready
- ✅ Postman installed (download from: https://www.postman.com/downloads/)

### Step 1: Create Project Folder
```bash
# In VS Code Terminal (Ctrl+`)
mkdir anaplan-mock-project
cd anaplan-mock-project
```

### Step 2: Copy Files
Copy ALL these files into your project folder:
- `mock_anaplan_server.py`
- `anaplan_bridge.py`
- `run_anaplan_workflow.py`
- `sample_input.csv`
- `requirements.txt`
- **Your existing `app.py`** (your Streamlit app)

### Step 3: Install Dependencies
```bash
# Open VS Code terminal and run:
pip install fastapi uvicorn python-multipart pydantic requests

# Also make sure your Streamlit dependencies are installed:
pip install streamlit pandas numpy
```

### Step 4: Start the Mock Anaplan Server
```bash
# Terminal 1 - Start the server
python mock_anaplan_server.py
```

You should see:
```
============================================================
  🚀 Mock Anaplan Server Starting...
============================================================
  📍 URL: http://localhost:8000
  📖 Docs: http://localhost:8000/docs
============================================================
```

**Leave this terminal running!**

### Step 5: Upload Data via Postman (Simulate Anaplan Receiving Data)

1. **Open Postman**
2. **Create a new request:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/v1/upload`
3. **Go to "Body" tab:**
   - Select `form-data`
   - Key: `file` (change type to "File" from dropdown)
   - Value: Select `sample_input.csv` from your computer
4. **Click "Send"**

**Expected Response:**
```json
{
  "job_id": "JOB-20240831-143022-1234",
  "status": "ready",
  "message": "Input file 'sample_input.csv' uploaded successfully..."
}
```

**Copy the `job_id` - you'll need it!**

### Step 6: Pull Data into Your Streamlit App

**Option A - Using the bridge script:**
```bash
# Terminal 2 - Pull data from Anaplan
python anaplan_bridge.py pull
```

This downloads the CSV to: `bridge_data/temp_input_from_anaplan.csv`

**Option B - Direct API call in Postman:**
- Method: `GET`
- URL: `http://localhost:8000/api/v1/download/JOB-XXXXX`
- (Replace JOB-XXXXX with your actual job ID)

### Step 7: Launch Your Streamlit App
```bash
# Terminal 3 - Launch your app
streamlit run app.py
```

**In your Streamlit app:**
1. Load the file: `bridge_data/temp_input_from_anaplan.csv`
2. Run your ML model as usual
3. **Download the forecast output** (save it somewhere you can find, like Desktop)

### Step 8: Push Output Back to Anaplan

**Option A - Using the bridge script:**
```bash
# In Terminal 2
python anaplan_bridge.py push "C:/Users/YourName/Downloads/forecast_output.csv"
```

**Option B - Using Postman:**
1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/output/JOB-XXXXX`
3. Body → form-data:
   - Key: `file` (type: File)
   - Value: Select your downloaded forecast output CSV
4. Click "Send"

**Expected Response:**
```json
{
  "success": true,
  "message": "Output uploaded to Anaplan successfully"
}
```

### Step 9: Verify in Postman

Check job status:
- Method: `GET`
- URL: `http://localhost:8000/api/v1/jobs/JOB-XXXXX`

Download the stored output:
- Method: `GET`
- URL: `http://localhost:8000/api/v1/output/JOB-XXXXX/download`

---

## 🎮 ALTERNATIVE: Use the Orchestrator (Easier!)

Instead of running steps manually, use the orchestrator:

```bash
# This runs the full workflow interactively
python run_anaplan_workflow.py
```

Or just start the server:
```bash
python run_anaplan_workflow.py server
```

---

## 📡 All API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/v1/upload` | POST | Upload input CSV to Anaplan |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/jobs/{job_id}` | GET | Get job status |
| `/api/v1/download/{job_id}` | GET | Download input file |
| `/api/v1/output/{job_id}` | POST | Upload forecast output |
| `/api/v1/output/{job_id}/download` | GET | Download stored output |
| `/api/v1/jobs/{job_id}` | DELETE | Delete job |

**Interactive docs:** http://localhost:8000/docs

---

## 🔧 Bridge Script Commands

```bash
# Check server status
python anaplan_bridge.py status

# Pull data from Anaplan
python anaplan_bridge.py pull
python anaplan_bridge.py pull JOB-XXXXX  # specific job

# Push output to Anaplan
python anaplan_bridge.py push output.csv

# List all jobs
python anaplan_bridge.py jobs
```

---

## 📂 Folder Structure After Setup

```
anaplan-mock-project/
│
├── app.py                          ← YOUR Streamlit app (UNCHANGED)
├── mock_anaplan_server.py          ← FastAPI server
├── anaplan_bridge.py               ← Bridge script
├── run_anaplan_workflow.py         ← Orchestrator
├── sample_input.csv                ← Demo data
├── requirements.txt                ← Dependencies
│
├── anaplan_uploads/                ← Server stores uploads here
├── anaplan_outputs/                ← Server stores outputs here
├── bridge_data/                    ← Bridge stores temp files here
│   ├── temp_input_from_anaplan.csv
│   └── current_job.json
```

---

## ⚡ Quick Test (No Streamlit)

Test the server without your Streamlit app:

```bash
# 1. Start server
python mock_anaplan_server.py

# 2. In another terminal, upload test data
curl -X POST -F "file=@sample_input.csv" http://localhost:8000/api/v1/upload

# 3. Download it back
curl -O http://localhost:8000/api/v1/download/JOB-XXXXX

# 4. Push a test output
curl -X POST -F "file=@sample_input.csv" http://localhost:8000/api/v1/output/JOB-XXXXX
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port 8000 already in use" | Kill existing process or change port in `mock_anaplan_server.py` |
| "Module not found" | Run `pip install fastapi uvicorn python-multipart requests` |
| "Connection refused" | Make sure server is running on localhost:8000 |
| Streamlit app won't load file | Check that `bridge_data/temp_input_from_anaplan.csv` exists |
| Postman shows error | Check server is running and URL is correct |

---

## 📝 Summary Flow

```
1. START SERVER → python mock_anaplan_server.py
2. UPLOAD DATA → Postman POST /api/v1/upload
3. PULL DATA   → python anaplan_bridge.py pull
4. RUN APP     → streamlit run app.py (load the pulled CSV)
5. DOWNLOAD    → Save output from Streamlit
6. PUSH OUTPUT → python anaplan_bridge.py push output.csv
7. VERIFY      → Postman GET /api/v1/jobs/JOB-XXXXX
```

**Your `app.py` is NEVER modified!** 🎉
