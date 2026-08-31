# Mock Anaplan ↔ Streamlit Integration — Step by Step

## What we built
- `anaplan_mock_server.py` — a fake "Anaplan" running on your laptop (FastAPI + uvicorn)
- `anaplan_client.py` — helper functions your `app.py` uses to talk to it
- `app_integration_snippet.py` — copy-paste code to add two buttons to your existing `app.py`
- `Mock_Anaplan.postman_collection.json` — ready-made Postman requests

## The flow
1. In **Postman**, you upload `input.csv` — pretending you're Anaplan sending data.
2. In **Streamlit** (`app.py`), you click "Pull input from Anaplan" — it downloads that file, runs your model, produces `output.csv`.
3. Still in **Streamlit**, you click "Push output to Anaplan" — it uploads `output.csv` to the mock server.
4. Back in **Postman**, you download `output.csv` to prove it arrived — pretending you're Anaplan receiving the forecast.

---

## PART A — Set up in VS Code

1. **Open VS Code**, open the folder that contains your `app.py`.
2. Copy these 3 files into that same folder:
   - `anaplan_mock_server.py`
   - `anaplan_client.py`
   - `Mock_Anaplan.postman_collection.json` (this one you'll use in Postman, not VS Code)
3. Open the built-in Terminal in VS Code: menu **Terminal → New Terminal**.
4. Install the needed packages (one time only) by typing:
   ```
   pip install fastapi uvicorn python-multipart requests streamlit pandas
   ```
   Press Enter and wait for it to finish.
5. Open `app.py` and paste in the two buttons from `app_integration_snippet.py`:
   - The "Pull input from Anaplan" button goes near where you currently drag-and-drop files.
   - The "Push output to Anaplan" button goes right after your model creates `output.csv`.
   - At the top of `app.py`, add this line with your other imports:
     ```python
     from anaplan_client import fetch_input_from_anaplan, push_output_to_anaplan, anaplan_status
     ```
6. Save `app.py`.

---

## PART B — Run the mock Anaplan server

1. In the VS Code terminal, type:
   ```
   uvicorn anaplan_mock_server:app --reload --port 8000
   ```
2. You should see a message saying it's running on `http://127.0.0.1:8000`. **Leave this terminal open** — closing it shuts the server down.
3. Open a browser and go to `http://127.0.0.1:8000` — you should see `{"status": "Mock Anaplan server is running"}`. That confirms it works.

---

## PART C — Load input data using Postman (simulating Anaplan)

1. Open **Postman**.
2. Click **Import** (top left) → choose the file `Mock_Anaplan.postman_collection.json` → Import.
3. You'll now see a folder called "Mock Anaplan Server" with 5 requests in the left sidebar.
4. Click on **"2. Upload input.csv to Anaplan"**.
5. Go to the **Body** tab → you'll see a row with key `file` and a **Select Files** button. Click it and choose your `input.csv` (the file you'd normally drag-and-drop into the Streamlit app).
6. Click the blue **Send** button.
7. You should get a response like:
   ```json
   {"message": "input.csv received and stored in mock Anaplan", ...}
   ```
   This means "Anaplan" now has your input data ready.

---

## PART D — Run your Streamlit app

1. Back in VS Code, open a **second** terminal (click the `+` icon in the terminal panel — don't close the first one, the server needs to keep running).
2. In this new terminal, type:
   ```
   streamlit run app.py
   ```
3. It will open in your browser (usually `http://localhost:8501`).
4. Click the **"Pull input from Anaplan"** button you added. It should download `input.csv` from the mock server and show a preview — this replaces manually dragging the file in.
5. Run your model/pipeline exactly as you normally do (Model → Dashboard → Results), so it produces `output.csv`.
6. Click the **"Push output to Anaplan"** button. You should see a green success message.

---

## PART E — Confirm the output landed in Anaplan (Postman again)

1. Go back to **Postman**.
2. Click **"4. Download output.csv from Anaplan (verify push)"**.
3. Click **Send**.
4. Click the **Save Response** option (or the download icon) to save the file, and open it — it should be the exact forecast output your Streamlit app just generated.

That confirms the full loop worked: **Anaplan → Streamlit (model runs) → Anaplan**.

---

## Notes
- This is a *mock* of Anaplan for local testing. To connect to real Anaplan later, you'd swap the URLs in `anaplan_client.py` for Anaplan's real API endpoints and add your Anaplan API credentials — the rest of the flow (fetch → run model → push) stays the same.
- If Postman says "could not send request", double check the mock server terminal (Part B) is still running.
- If Streamlit says "Anaplan server not reachable", same thing — make sure `uvicorn` is running in its own terminal.
