# Zero-Code-Change Integration — Step by Step

Use this instead of editing app.py. It drives your app the same way you
would by hand, from an outside script.

## 1. Install extra packages (one time)
In VS Code terminal:
```
pip install selenium webdriver-manager requests
```
(Make sure Google Chrome is installed on your PC — the script controls it directly.)

## 2. Put `orchestrator.py` in the same folder as `app.py`
Also keep `anaplan_mock_server.py` there (from before).

## 3. Check the 3 settings at the top of orchestrator.py
```python
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_WATCH_FOLDER = os.path.dirname(os.path.abspath(__file__))  # where output.csv appears
OUTPUT_FILENAME = "output.csv"
```
Change `OUTPUT_WATCH_FOLDER` only if your app saves the results file somewhere else.

## 4. Start the mock Anaplan server (Terminal 1)
```
uvicorn anaplan_mock_server:app --reload --port 8000
```

## 5. Load input data into "Anaplan" via Postman
Same as before: open Postman → Mock Anaplan Server collection → request
"2. Upload input.csv to Anaplan" → attach your file → Send.

## 6. Start your Streamlit app, untouched (Terminal 2)
```
streamlit run app.py
```
Leave it running in the browser tab it opens.

## 7. Run the orchestrator (Terminal 3)
```
python orchestrator.py
```
Watch what happens:
- It fetches input.csv from Anaplan.
- It opens a **new** Chrome window pointed at your app and drops the file into the uploader for you.
- If your app needs manual clicks (e.g., a "Run Model" button), click them in that Chrome window — the script is just watching for the output file, it doesn't need control of every click.
- Once `output.csv` shows up in the folder, it automatically pushes it to Anaplan and prints "DONE."

## 8. Confirm in Postman
Request "4. Download output.csv from Anaplan" → Send → save/open the file to confirm it matches what your app produced.

---

### If your app never actually saves output.csv to disk
Some Streamlit apps only show results in the browser and offer a
"Download" button rather than auto-saving a file. In that case, tell me
where the download goes (or if there's a specific button to click) and
I'll adjust the script to click that button automatically too.
