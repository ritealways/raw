# Mock Anaplan Server — Step-by-Step Guide

This is a pretend ("mock") version of an Anaplan integration. It does NOT
connect to real Anaplan. Instead:

- **Import** = a script reads an Excel file from a local folder that is
  standing in for Anaplan, and saves a copy into an "imported" folder.
- **Export** = a script takes an Excel file you upload in Postman and
  saves it into a folder that is standing in for Anaplan's inbox.

This lets you practice/demo the full import → process → export flow
without needing real Anaplan credentials.

## What's in this folder

| File | What it does |
|---|---|
| `anaplan_server.py` | The server (Script 1). Run this first — it stays running and listens for requests. |
| `import_from_anaplan.py` | Script 2 — pulls the mock "Anaplan" file into your local `imported` folder. |
| `Mock_Anaplan.postman_collection.json` | Script 3 — import this into Postman to get ready-made requests. |
| `export_to_anaplan.py` | Script 4 — pushes a file you upload into the mock "Anaplan export" folder. |
| `generate_sample_excel.py` | Supporting file — creates sample Excel files so you have something to test with. |
| `requirements.txt` | Supporting file — list of Python packages needed. |
| `data/` | Supporting folders — this is where all the Excel files live and get saved. |

The `data` folder has 4 sub-folders:
- `data/anaplan_source` — pretend this is "inside Anaplan" (the source data lives here)
- `data/imported` — where imported files land after Script 2 runs
- `data/to_export` — put files here that you want to push out (used for testing the export)
- `data/anaplan_export` — pretend this is "Anaplan's inbox" (final destination for exported files)

---

## PART A — One-time setup in VS Code

1. **Install Python** (if you don't already have it): go to python.org,
   download Python 3.10+ for your OS, and install it. During install on
   Windows, tick the box "Add Python to PATH".

2. **Install VS Code** (if you don't already have it) from
   code.visualstudio.com.

3. **Open the project folder in VS Code**:
   - Unzip the folder you downloaded (`anaplan_mock_project`) somewhere
     easy to find, like your Desktop.
   - Open VS Code.
   - Go to `File > Open Folder...` and select the `anaplan_mock_project`
     folder.

4. **Open a terminal inside VS Code**:
   - Go to the top menu: `Terminal > New Terminal`.
   - A black/blank command-line box will appear at the bottom of VS Code.
     This is where you'll type commands.

5. **Install the required Python packages**. In that terminal, type:
   ```
   pip install -r requirements.txt
   ```
   and press Enter. Wait for it to finish (it installs Flask, pandas,
   and openpyxl).

6. **Create the sample Excel files** to test with. In the same terminal, type:
   ```
   python generate_sample_excel.py
   ```
   and press Enter. You should see two lines confirming two Excel files
   were created inside the `data` folder.

---

## PART B — Start the mock server

1. In the same VS Code terminal, type:
   ```
   python anaplan_server.py
   ```
   and press Enter.

2. You should see a message saying the server is starting, along with
   web addresses like `http://127.0.0.1:5000/health`.

3. **Leave this terminal running** — don't close it and don't press
   Ctrl+C. This is your live "server" that Postman will talk to.

4. (Optional check) Open any web browser and go to:
   ```
   http://127.0.0.1:5000/health
   ```
   You should see a small message confirming the server is running. If
   you see that, everything is working correctly so far.

---

## PART C — Set up Postman

1. **Install Postman** (if you don't have it) from postman.com/downloads.

2. **Open Postman**.

3. **Import the ready-made collection**:
   - Click the `Import` button (usually top-left).
   - Choose `Upload Files`, and select `Mock_Anaplan.postman_collection.json`
     from the project folder.
   - Click `Import`. You should now see a collection called
     "Mock Anaplan Integration" in the left sidebar, with 3 requests
     inside it: `0. Health Check`, `1. Import from Anaplan`, and
     `2. Export to Anaplan`.

---

## PART D — Test the IMPORT (pulling data from mock Anaplan)

1. In Postman's left sidebar, click on the request named
   **"1. Import from Anaplan"**.

2. Click the blue **Send** button.

3. You should get a response at the bottom of the screen that looks
   something like:
   ```
   {
     "status": "success",
     "message": "Data imported from (mock) Anaplan successfully.",
     "rows": 4,
     "columns": ["Region", "Product", "Month", "Actuals"]
   }
   ```

4. Go check the `data/imported` folder in VS Code's file explorer
   (left sidebar) — you'll see a new Excel file appeared there, with a
   timestamp in its name. That's the "pulled from Anaplan" file.

---

## PART E — Test the EXPORT (pushing data back to mock Anaplan)

1. In Postman, click on the request named **"2. Export to Anaplan"**.

2. Click on the **Body** tab (below the address bar in Postman).

3. You'll see a row with the key `file` and a **Select Files** button
   on the right. Click **Select Files**.

4. In the file picker, navigate to the project folder and choose:
   ```
   data/to_export/output_data.xlsx
   ```

5. Click the blue **Send** button.

6. You should get a response like:
   ```
   {
     "status": "success",
     "message": "File exported to (mock) Anaplan successfully.",
     "rows": 4,
     "columns": ["Region", "Product", "Month", "Forecast"]
   }
   ```

7. Go check the `data/anaplan_export` folder in VS Code — you'll see
   the file you uploaded now sitting there with a timestamp. That's the
   "pushed to Anaplan" file.

---

## Trying it with your OWN Excel files

- To test import with your own data: replace the file at
  `data/anaplan_source/input_data.xlsx` with your own Excel file (keep
  the same file name), then send the "Import from Anaplan" request
  again in Postman.
- To test export with your own data: in Postman's "Export to Anaplan"
  request, just pick a different `.xlsx` file when you click
  **Select Files** — it doesn't have to be from the `to_export` folder.

## Stopping the server

When you're done, click into the VS Code terminal running the server
and press `Ctrl + C` to stop it.

## Troubleshooting

- **"python is not recognized"** → Python isn't installed or wasn't
  added to PATH. Reinstall Python and make sure to check "Add Python
  to PATH" during setup.
- **Postman says "Could not send request" / connection refused** → The
  server isn't running. Go back to VS Code and make sure
  `python anaplan_server.py` is still running in the terminal.
- **Import fails with "Could not find input_data.xlsx"** → Run
  `python generate_sample_excel.py` again to recreate the sample files.
- **Port 5000 already in use** → Another program is using that port.
  Close it, or open `anaplan_server.py` and change `port=5000` to
  something else like `port=5050` (and update the URLs in Postman to match).
