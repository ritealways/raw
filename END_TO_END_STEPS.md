# End-to-End Steps: Mock Anaplan ↔ Streamlit Integration

This guide walks through running the mock Anaplan server, pulling input data,
running your Streamlit app, and pushing results back — using VS Code and Postman.

---

## What you need before starting

- VS Code installed
- Python installed (3.8+)
- Postman installed
- Your `app.py` (Streamlit app)
- A sample input CSV (e.g. `WC_Premium_Dummy_Data.csv`)

---

## Step 1 — Set up the project folder

1. Create a folder, e.g. `anaplan_mock_project`.
2. Put these files inside it:
   - `anaplan_mock_server.py`
   - `pull_from_anaplan.py`
   - `push_to_anaplan.py`
   - `Mock_Anaplan.postman_collection.json`
   - `requirements.txt`
   - your existing `app.py`
3. Inside that folder, create a subfolder called `data`.
   This is where `input.csv` and `output.csv` will live.

Your folder should look like this:

```
anaplan_mock_project/
├── app.py
├── anaplan_mock_server.py
├── pull_from_anaplan.py
├── push_to_anaplan.py
├── requirements.txt
├── Mock_Anaplan.postman_collection.json
└── data/
```

---

## Step 2 — Install the required packages

Open a terminal in VS Code (Terminal → New Terminal), make sure you're inside
the project folder, then run:

```
pip install -r requirements.txt
```

This installs Flask, Requests, Streamlit, and Pandas.

---

## Step 3 — Start the mock Anaplan server (Terminal 1)

In VS Code, open a terminal and run:

```
python anaplan_mock_server.py
```

Leave this terminal running the whole time — it's now acting as a
fake Anaplan at `http://localhost:5000`.

You should see:
```
Mock Anaplan server starting at http://localhost:5000
```

---

## Step 4 — Load a sample input file into "Anaplan" (Postman)

1. Open Postman.
2. Click **Import** → select `Mock_Anaplan.postman_collection.json`.
3. Open the request **"2. Upload Input Data (simulate Anaplan has data)"**.
4. Go to the **Body** tab → it's set to `form-data`.
5. Next to the `file` key, click **Select Files** and choose your sample CSV
   (e.g. `WC_Premium_Dummy_Data.csv`).
6. Click **Send**.

You should get back:
```json
{ "message": "Input data received by mock Anaplan." }
```

This simulates Anaplan having source data ready for you to pull.

---

## Step 5 — Pull the data into your project (Terminal 2)

Open a **second** terminal in VS Code (keep the server running in Terminal 1)
and run:

```
python pull_from_anaplan.py
```

This downloads the file from the mock Anaplan server and saves it as:
```
data/input.csv
```

---

## Step 6 — Run your Streamlit app (Terminal 2)

In the same or a new terminal:

```
streamlit run app.py
```

This opens a browser tab.

1. Drag and drop `data/input.csv` into the upload box (same as your screenshot).
2. Run your model as usual.
3. View results on the Dashboard/Results page.
4. Export/save the results as:
   ```
   data/output.csv
   ```
   (If `app.py` doesn't already have a "Download results as CSV" button,
   this step needs to be added — share `app.py` and this can be built in.)

---

## Step 7 — Push the forecast back to "Anaplan"

**Option A — Script (Terminal 3):**
```
python push_to_anaplan.py
```

**Option B — Postman:**
1. Open request **"4. Push Output Data (push forecast INTO Anaplan)"**.
2. Body tab → attach `data/output.csv` as the `file`.
3. Click **Send**.

You should get back:
```json
{ "message": "Forecast output received by mock Anaplan." }
```

---

## Step 8 — Verify the forecast arrived

In Postman, run request **"5. Get Output Data (verify forecast received)"**.

This downloads the file back from the mock server — if it downloads
successfully, the full round trip worked:

**Anaplan (mock) → pull → Streamlit app → push → Anaplan (mock)**

---

## Quick recap of terminals used

| Terminal | Purpose | Command |
|---|---|---|
| 1 | Runs the mock Anaplan server | `python anaplan_mock_server.py` |
| 2 | Pulls input, then runs Streamlit | `python pull_from_anaplan.py` then `streamlit run app.py` |
| 3 (optional) | Pushes output back | `python push_to_anaplan.py` |

---

## Troubleshooting

- **"Connection refused" in Postman or scripts** → Terminal 1 (the mock server)
  isn't running. Start it first.
- **"No input file uploaded yet"** → run Step 4 (Postman upload) before Step 5 (pull script).
- **"No output file received yet"** → make sure `data/output.csv` exists before Step 7.
- **Port 5000 already in use** → close whatever else is using it, or change
  the port number in `anaplan_mock_server.py` (and update the URLs in the
  scripts and Postman collection to match).
