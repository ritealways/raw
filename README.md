# Mock Anaplan + wc_lgbm.py Integration — Step-by-Step Guide

This package gives you three files:

| File | What it is |
|---|---|
| `mock_server.py` | A fake local Anaplan API. Serves your real `input_excel.xlsx` and stores whatever gets pushed back as your real `Output_excel.xlsx` |
| `pipeline.py` | Pulls `input_excel.xlsx` from the mock Anaplan, runs **your** `wc_lgbm.py` on it, pushes the resulting `Output_excel.xlsx` back |
| `Anaplan_Mock_Server.postman_collection.json` | A ready-made Postman collection so you can click through every API call by hand |

**Nothing here generates fake data.** The mock server only reads/writes the two real Excel files you point it at, and the pipeline only calls your existing `wc_lgbm.py` — it doesn't do any forecasting itself.

The flow:

```
Anaplan (mock)  --export input_excel.xlsx-->  pipeline.py
                                                    |
                                          calls YOUR wc_lgbm.py
                                          (input_excel -> Output_excel)
                                                    |
Anaplan (mock)  <--import Output_excel.xlsx--  pipeline.py
```

Everything runs locally on `http://127.0.0.1:8000` on your own machine — no real Anaplan account needed for testing.

---

## Part A — One-time setup in VS Code

1. **Install Python** (if you don't have it): python.org/downloads → download Python 3.11+ → run installer → tick **"Add Python to PATH"** on the first screen.

2. **Install VS Code**: code.visualstudio.com/download

3. **Install the Python extension**: VS Code → Extensions icon (left sidebar) → search "Python" → install the Microsoft one.

4. **Put all your files in one folder.** Create a project folder (e.g. `anaplan_pipeline`) and put these inside it:
   - `mock_server.py`
   - `pipeline.py`
   - `Anaplan_Mock_Server.postman_collection.json`
   - `requirements.txt`
   - **your own `wc_lgbm.py`**
   - **your own `input_excel.xlsx`**

5. **Open that folder in VS Code**: File → Open Folder → select it.

6. **Open a terminal in VS Code**: Terminal menu → New Terminal.

7. **Create and activate a virtual environment**:
   ```
   python -m venv venv
   ```
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

   You'll see `(venv)` appear at the start of the terminal line once it's active.

8. **Install the required packages**:
   ```
   pip install -r requirements.txt
   ```

---

## Part B — Point the scripts at YOUR real files (do this once)

1. **Open `mock_server.py`** in VS Code. Near the top you'll see:
   ```python
   INPUT_EXCEL_PATH = "./data/input_excel.xlsx"
   OUTPUT_EXCEL_PATH = "./data/Output_excel.xlsx"
   ```
   Change these two lines to the actual location of your files. Easiest option: create a `data` subfolder inside your project folder and put your `input_excel.xlsx` there (the path above already expects that). Otherwise, replace with a full path, e.g.:
   ```python
   INPUT_EXCEL_PATH = "C:/Users/yourname/Documents/input_excel.xlsx"
   OUTPUT_EXCEL_PATH = "C:/Users/yourname/Documents/Output_excel.xlsx"
   ```
   `Output_excel.xlsx` doesn't need to exist yet — it gets created automatically the first time a forecast is pushed.

2. **Open `pipeline.py`** in VS Code. Near the top you'll see:
   ```python
   WC_LGBM_SCRIPT_PATH = "./wc_lgbm.py"
   ```
   Change this if your `wc_lgbm.py` lives somewhere else, e.g. a full path.

3. **Check how your `wc_lgbm.py` normally gets run.** `pipeline.py` calls it like this by default:
   ```
   python wc_lgbm.py --input <path> --output <path>
   ```
   - **If your script already accepts `--input` and `--output` flags** (or you run it that way normally) — you're done, no changes needed.
   - **If your script uses different argument names**, or reads/writes fixed file paths, or is meant to be imported rather than run from the command line — open `pipeline.py`, find the `call_wc_lgbm()` function (it has clear comments marking **OPTION A** and **OPTION B**), and adjust it to match how you actually run `wc_lgbm.py`. This is the *only* part of the pipeline that depends on your script's specific interface.

---

## Part C — Run the mock Anaplan server

1. In the VS Code terminal (with `(venv)` active):
   ```
   uvicorn mock_server:app --reload --port 8000
   ```
2. You should see `Uvicorn running on http://127.0.0.1:8000`. **Leave this terminal open** — this is your stand-in "Anaplan" and needs to stay running.
3. Open a browser to **http://127.0.0.1:8000/** — check that `"input_excel_found": true` appears in the response. If it says `false`, your `INPUT_EXCEL_PATH` in `mock_server.py` isn't pointing at the right place — fix it and save (the server auto-reloads).
4. You can also browse **http://127.0.0.1:8000/docs** for an interactive page listing every endpoint.

> If port 8000 is already in use on your machine, change `--port 8000` to e.g. `--port 8001`, and also update `BASE_URL` at the top of `pipeline.py` and the `base_url` variable in the Postman collection to match.

---

## Part D — Run the pipeline

1. Open a **second** VS Code terminal (keep the server running in the first one). Activate the virtual environment again:
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

2. Run:
   ```
   python pipeline.py
   ```

3. It will print, step by step:
   - STEP 1: Logging in
   - STEP 2: Downloading your real `input_excel.xlsx` from the mock Anaplan
   - STEP 3: Running your `wc_lgbm.py` on it
   - STEP 4: Uploading the resulting `Output_excel.xlsx` back into the mock Anaplan
   - STEP 5: Downloading it back out again to confirm it saved

4. On success you'll see: `Done. Input pulled from Anaplan -> forecast generated by wc_lgbm.py -> pushed back to Anaplan.`

5. Your finished forecast is now sitting at the `OUTPUT_EXCEL_PATH` you set in `mock_server.py` (Part B, step 1) — open it in Excel to check it.

---

## Part E — Test the API by hand in Postman (no coding)

This lets you click through the same steps one at a time, so you can see exactly what's being sent/received.

1. **Install Postman**: postman.com/downloads (you can use it without creating an account for local testing).

2. **Import the collection**: click **Import** (top-left) → drag in `Anaplan_Mock_Server.postman_collection.json`. You'll see a collection called **"Anaplan Mock Server"** with 10 numbered requests.

3. **Make sure the mock server is running** (Part C above).

4. **Run the requests in order**, opening each and clicking **Send**:

   | # | Request | What happens |
   |---|---|---|
   | 1 | Health Check | Confirms the server is alive and shows whether it can find your input file |
   | 2 | Login | Gets a token and auto-saves it for later requests |
   | 3 | List Workspaces | Shows the fake workspace |
   | 4 | List Models | Shows the fake model |
   | 5 | List Files | Shows the input/output file entries |
   | 6 | Download input_excel.xlsx (Export) | Downloads your real input file — click **Send**, then **Save Response → Save to a file** to download it and check it's correct |
   | 7 | Upload Output_excel.xlsx (Import step 1) | **Before sending**: open the **Body** tab of this request, make sure **binary** is selected, click **Select File**, and choose the real `Output_excel.xlsx` your `wc_lgbm.py` produced on your computer. Then click **Send**. |
   | 8 | Run Import Process (Import step 2) | Tells the mock Anaplan to save the uploaded file — auto-saves the returned `task_id` |
   | 9 | Check Task Status | Confirms it finished (`status: COMPLETE`) |
   | 10 | Download Output_excel.xlsx (Verify) | Downloads the file back out, proving it was saved. Use **Save Response → Save to a file** to check it. |

   The token from request #2 and task ID from #8 are reused automatically in later requests — no manual copy/paste needed.

---

## Troubleshooting

- **"input_excel not found at '...'"** → `INPUT_EXCEL_PATH` in `mock_server.py` doesn't point at your real file. Fix the path and save.
- **"Could not connect to the mock Anaplan server"** → `mock_server.py` isn't running, or it's on a different port than `BASE_URL` in `pipeline.py`.
- **"wc_lgbm.py did not run successfully"** → your script's command-line arguments don't match `--input`/`--output`. Edit `call_wc_lgbm()` in `pipeline.py` (see Part B, step 3).
- **"expected wc_lgbm.py to create '...' but it wasn't found"** → your script ran but didn't write its result to the exact output path it was given. Check where your script actually saves its file, and either change your script to accept the output path, or adjust `GENERATED_OUTPUT_PATH` handling in `pipeline.py` to match where it actually writes.
- **Postman requests return 401 Unauthorized** → run request #2 (Login) again — the token may not have been saved yet.
- **`ModuleNotFoundError`** → your virtual environment isn't activated, or `pip install -r requirements.txt` hasn't been run in it.
- **Port already in use** → change the port everywhere (server command, `BASE_URL` in `pipeline.py`, and `base_url` in Postman) to e.g. 8001.
- **Fresh start** → stop the server (Ctrl+C) and restart it. Tokens/tasks reset each time (in-memory only); your Excel files on disk are untouched unless a new forecast is pushed.

---

## What's mocked vs. what's real

`mock_server.py` copies the shape of Anaplan's real REST API (login, workspace/model listing, file export, chunked file import, process execution, task polling) so this integration pattern carries over almost unchanged once you connect to a real Anaplan tenant — you'd swap the login step for real Anaplan credentials, `BASE_URL` for Anaplan's real API URL, and the workspace/model/file/process IDs for your real ones. The Excel files themselves, and your `wc_lgbm.py` forecasting logic, don't need to change at all.
