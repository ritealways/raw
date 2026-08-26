# Mock Anaplan + LightGBM Forecast Integration — Step-by-Step Guide

This package gives you three things:

| File | What it is |
|---|---|
| `mock_anaplan_server.py` | A fake local Anaplan API (runs on your laptop) |
| `wc_lightgbm_forecast.py` | Your forecasting script — pulls data from the mock Anaplan, runs LightGBM, pushes results back |
| `Anaplan_Mock_Server.postman_collection.json` | A ready-made Postman collection so you can click through every API call by hand |

The flow it simulates:

```
Anaplan (mock)  --export input data-->  wc_lightgbm_forecast.py
                                              |
                                        trains LightGBM
                                        (P10 / P50 / P90)
                                              |
Anaplan (mock)  <--import forecast output--  wc_lightgbm_forecast.py
```

No real Anaplan account is needed. Everything runs on `http://127.0.0.1:8000` on your own machine.

---

## Part A — One-time setup in VS Code

1. **Install Python** (if you don't have it): go to python.org/downloads, download Python 3.11+, run the installer. On the first install screen, tick **"Add Python to PATH"**.

2. **Install VS Code**: code.visualstudio.com/download.

3. **Install the Python extension in VS Code**: open VS Code → click the Extensions icon on the left sidebar (four squares) → search "Python" → install the Microsoft one.

4. **Open this project folder in VS Code**:
   - File → Open Folder → select the folder containing these files.

5. **Open a terminal inside VS Code**:
   - Menu bar → Terminal → New Terminal. A terminal panel opens at the bottom.

6. **Create a virtual environment (keeps this project's packages separate from everything else)**:
   ```
   python -m venv venv
   ```
   Then activate it:
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

   You'll know it worked because you'll see `(venv)` appear at the start of the terminal line.

7. **Install the required packages**:
   ```
   pip install -r requirements.txt
   ```
   This installs FastAPI, Uvicorn, pandas, LightGBM, scikit-learn, and requests. Takes 1–3 minutes.

---

## Part B — Run the mock Anaplan server

1. In the VS Code terminal (with `(venv)` active), run:
   ```
   uvicorn mock_anaplan_server:app --reload --port 8000
   ```
2. You should see something like:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```
3. **Leave this terminal running** — this is your "Anaplan" pretending to be alive. Don't close it.
4. Open a web browser and go to **http://127.0.0.1:8000/docs** — you'll see a nice interactive page listing every fake Anaplan endpoint. You can click "Try it out" on any of them right there if you want.

> Tip: If port 8000 is already used by something else on your machine, change `--port 8000` to `--port 8001` (and update `BASE_URL` in `wc_lightgbm_forecast.py` and the Postman collection's `base_url` variable to match).

---

## Part C — Run the forecasting script

1. Open a **second** terminal in VS Code (Terminal → New Terminal — keep the server running in the first one). Activate the same virtual environment again:
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

2. Run:
   ```
   python wc_lightgbm_forecast.py
   ```

3. Watch the output. It will print, step by step:
   - STEP 1: Logging in and getting a security token
   - STEP 2: Downloading the historical input data (Region/Channel/Industry/Account Size/Payroll/Avg Wage/etc.) — this is the mock version of the "Input data to model" tab in your spreadsheet
   - STEP 3: Training 3 LightGBM models (low estimate, typical estimate, high estimate)
   - STEP 4–5: Building next-3-months forecasts for every Region/Channel/Industry/Account Size combination and predicting P10 / P50 (Median) / P90
   - STEP 6: Uploading and importing that forecast back into the mock Anaplan
   - STEP 7: Downloading it back out again to prove it saved correctly — this mirrors the "forecasted output data from model" tab in your spreadsheet

4. If everything worked you'll see `Done. Forecast successfully pulled, generated, and pushed to mock Anaplan.` at the bottom.

**To forecast more/fewer months**, open `wc_lightgbm_forecast.py`, find the line near the top:
```python
FORECAST_MONTHS = 3
```
change `3` to whatever number you want, save, and re-run.

**To connect this to your REAL Anaplan tenant later**, you'd only need to change three things in `wc_lightgbm_forecast.py`:
- `BASE_URL` → your real Anaplan API base URL
- the login step → use your real Anaplan credentials/OAuth app
- the workspace/model/file/process IDs → your real IDs (found in Anaplan under Workspace Administration)

The rest of the script (the LightGBM training and prediction logic) doesn't need to change.

---

## Part D — Test the API by hand in Postman (no coding)

This lets you click through the exact same steps the Python script does, one request at a time, so you can see what's happening "under the hood."

1. **Install Postman**: postman.com/downloads. Open it, skip/close any sign-up prompts (you can use it without an account for local testing).

2. **Import the collection**:
   - Click **Import** (top-left button).
   - Drag in the file `Anaplan_Mock_Server.postman_collection.json` (or click "Choose Files" and select it).
   - You'll now see a collection called **"Anaplan Mock Server"** in the left sidebar with 10 numbered requests.

3. **Make sure the mock server is running** (Part B above — keep that terminal open).

4. **Run the requests in order, top to bottom**, by opening each one and clicking the blue **Send** button:

   | # | Request | What happens |
   |---|---|---|
   | 1 | Health Check | Confirms the server is alive |
   | 2 | Login (get token) | Gets a security token and automatically saves it for the next requests |
   | 3 | List Workspaces | Shows the fake workspace |
   | 4 | List Models | Shows the fake model inside it |
   | 5 | List Files | Shows the input file and the output file |
   | 6 | Download Input Data (Export) | Downloads the CSV of historical data — the same as what the script pulls in Step 2 |
   | 7 | Upload Forecast Chunk (Import step 1) | Uploads a sample forecast CSV (you can edit the "Body" tab to paste in your own numbers) |
   | 8 | Run Import Process (Import step 2) | Tells the mock Anaplan to "load" the uploaded data — saves the returned `task_id` automatically |
   | 9 | Check Task Status | Confirms the import finished (`status: COMPLETE`) |
   | 10 | Download Forecast Output (Verify) | Downloads the forecast data back out, proving it was saved |

   You do **not** need to manually copy the token — request #2 automatically stores it in a Postman variable, and every later request reuses it.

5. **To push your own numbers instead of the sample**: open request **7**, go to its **Body** tab, and replace the CSV text with your own rows (same column headers: `Region,Channel,Industry_Class,Account_Size,Month,P10,P50_Median,P90`), then run requests 7 → 8 → 9 → 10 again.

---

## Troubleshooting

- **"Could not connect to the mock Anaplan server"** when running the Python script → the server (Part B) isn't running, or it's on a different port than `BASE_URL` in the script.
- **Postman requests return 401 Unauthorized** → run request #2 (Login) again first — the token may not have been saved.
- **`ModuleNotFoundError`** when running either Python file → your virtual environment isn't activated, or `pip install -r requirements.txt` wasn't run in it.
- **Port already in use** → close whatever else is using port 8000, or change the port everywhere (server command, `BASE_URL`, and Postman's `base_url` variable) to something like 8001.
- **Want a fresh start?** Just stop the server (Ctrl+C in its terminal) and start it again — all the fake data resets since it's stored in memory, not saved permanently.

---

## What's mocked vs. what's real

This mock server copies the **shape** of Anaplan's real REST API (login, workspaces, models, file export/import, process execution, task polling — same endpoints/patterns described in the reference guide you provided) so your integration code will look almost identical when you point it at a real tenant. What it does **not** do: real Anaplan security, real chunked uploads for huge files, rate limiting, or persistent storage between restarts. It's meant purely for local development/testing before you have real Anaplan credentials.
