# Mock Anaplan Integration Project

## Project Structure
- `server.py`: Flask application mocking the Anaplan REST API for file download & upload.
- `import_from_anaplan.py`: Client script downloading Excel data from Anaplan to `local_storage/downloaded_inputs/`.
- `export_to_anaplan.py`: Client script pushing processed Excel data to `anaplan_storage/export_target/`.
- `Anaplan_Mock_Collection.json`: Ready-to-import Postman collection.
- `generate_sample_data.py`: Creates starter Excel workbooks.
- `anaplan_storage/`: Simulates Anaplan cloud file storage.
- `local_storage/`: Simulates local pipeline file storage.

## How to Run in VS Code
1. Open VS Code and open this folder (`File > Open Folder...`).
2. Open terminal (`Ctrl + ` `) and install dependencies:
   `pip install -r requirements.txt`
3. Run the mock Anaplan server:
   `python server.py`
4. Open a second terminal window:
   - Run import: `python import_from_anaplan.py`
   - Run export: `python export_to_anaplan.py`

## How to Use with Postman
1. Open Postman, click **Import**, and select `Anaplan_Mock_Collection.json`.
2. Send request `1. Health Check`.
3. Send request `2. Download Excel from Anaplan` (use **Send and Download** to save file).
4. Send request `3. Upload Excel to Anaplan` (select an Excel file under Body -> form-data -> file).
