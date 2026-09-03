# Mock Anaplan Server - Complete Integration Setup

A simple mock server that simulates Anaplan integration via REST API. You can import Excel data FROM Anaplan and export processed Excel data TO Anaplan, all through Postman or Python scripts.

---

## Project Structure

```
anaplan_mock_server/
├── server.py                          # Main Flask REST API Server
├── import_from_anaplan.py             # Script to import data from Anaplan
├── export_to_anaplan.py               # Script to export data to Anaplan
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
├── input_from_anaplan/               # Folder: Files imported FROM Anaplan
├── output_to_anaplan/                # Folder: Files exported TO Anaplan
├── processed_data/                   # Folder: Processed/transformed files
├── source_files/                     # Folder: Mock Anaplan source files
└── postman_collections/
    └── Mock_Anaplan_Server_API.postman_collection.json
```

---

## Step-by-Step Setup (For Beginners)

### Step 1: Install Python and VS Code

1. **Install Python** (if not already installed):
   - Go to https://python.org/downloads
   - Download Python 3.9 or higher
   - During installation, **CHECK** "Add Python to PATH"
   - Verify: Open Command Prompt, type `python --version`

2. **Install VS Code** (if not already installed):
   - Go to https://code.visualstudio.com/download
   - Download and install for your OS
   - Install Python extension: Open VS Code > Extensions (left sidebar) > Search "Python" > Install "Python" by Microsoft

### Step 2: Download This Project

1. Extract the `anaplan_mock_server` folder to your Desktop or Documents
2. Open VS Code
3. Click **File** > **Open Folder** > Select the `anaplan_mock_server` folder
4. You should see all files in the Explorer panel (left side)

### Step 3: Install Required Packages

**Option A: Using VS Code Terminal**
1. In VS Code, press `Ctrl + backtick` (backtick key, top-left of keyboard) to open Terminal
2. Make sure you are in the project folder (you should see the path ending with `anaplan_mock_server`)
3. Run this command:
   ```bash
   pip install -r requirements.txt
   ```

**Option B: Using Command Prompt**
1. Open Command Prompt
2. Navigate to the project folder:
   ```bash
   cd C:\Users\YourName\Desktop\anaplan_mock_server
   ```
3. Run:
   ```bash
   pip install -r requirements.txt
   ```

Wait for installation to complete. You should see "Successfully installed" messages.

---

## How to Run the Scripts

### Script 1: Start the Server (MUST RUN FIRST!)

**What it does:** Starts a local web server that listens for API requests from Postman.

**How to run:**
1. In VS Code, open `server.py`
2. Click the **Run** button (triangle icon) in top-right corner, OR
3. Open Terminal and type:
   ```bash
   python server.py
   ```

**What you should see:**
```
============================================================
  MOCK ANAPLAN SERVER
============================================================
Server starting at: http://localhost:5000
Input folder:  ...input_from_anaplan
Output folder: ...output_to_anaplan
...
Press CTRL+C to stop the server
```

**IMPORTANT:** Keep this terminal window OPEN. The server must run continuously.

---

### Script 2: Import from Anaplan (Standalone)

**What it does:** Simulates reading data from Anaplan and saving it to the input folder.

**How to run:**
1. Open a **NEW** terminal (do not close the server terminal!)
   - In VS Code: Click the **+** button in the Terminal panel
2. Run:
   ```bash
   python import_from_anaplan.py
   ```

**What happens:**
- Creates a sample Excel file (if no source file exists)
- Copies it to `input_from_anaplan` folder
- Shows file contents and statistics

**Advanced options:**
```bash
# Import a specific file
python import_from_anaplan.py --file "C:\path\to\your\file.xlsx"

# List all imported files
python import_from_anaplan.py --list
```

---

### Script 3: Export to Anaplan (Standalone)

**What it does:** Processes data and saves it to the output folder (simulating export to Anaplan).

**How to run:**
1. Open a **NEW** terminal
2. Run:
   ```bash
   python export_to_anaplan.py
   ```

**What happens:**
- Reads the latest file from input folder
- Adds metadata, validates data, calculates totals
- Saves processed file to `output_to_anaplan` folder
- Generates an export report

**Advanced options:**
```bash
# Process a specific file
python export_to_anaplan.py --file "input_from_anaplan\your_file.xlsx"

# Custom output filename
python export_to_anaplan.py --output "my_export.xlsx"

# List all exported files
python export_to_anaplan.py --list
```

---

## How to Use with Postman

### Step 1: Install Postman
1. Go to https://www.postman.com/downloads/
2. Download and install Postman for your OS
3. Create a free account (or skip)

### Step 2: Import the Collection
1. Open Postman
2. Click **Import** button (top-left)
3. Select **File** tab
4. Click **Upload Files**
5. Navigate to `anaplan_mock_server/postman_collections/`
6. Select `Mock_Anaplan_Server_API.postman_collection.json`
7. Click **Import**

You should see "Mock Anaplan Server API" collection in your sidebar.

### Step 3: Start the Server
Make sure `server.py` is running (see Script 1 above).

### Step 4: Test the API Endpoints

Follow this order for a complete workflow:

#### 1. Health Check (Test Connection)
- Click on **"1. Health Check"**
- Click **Send** (blue button)
- Expected result: JSON showing "status": "healthy"

#### 2. Import from Anaplan (Upload File)
- Click on **"2. Import from Anaplan (Upload File)"**
- Under **Body** tab, make sure "form-data" is selected
- Click on the **"file"** row
- On the right side, change from "Text" to **"File"**
- Click **Select Files** and choose any Excel file (.xlsx)
- Click **Send**
- Expected result: JSON showing "success": true, with file info
- Check: The file is now saved in `input_from_anaplan` folder

#### 3. List Imported Files
- Click on **"3. List Imported Files (Input)"**
- Click **Send**
- Expected result: JSON list of all imported files

#### 4. Process File (Optional)
- Click on **"4. Process File"**
- In the URL, replace the filename with your actual imported file name
  - Example: Change `20260101_120000_sales_data.xlsx` to your actual filename
  - You can find the exact name from Step 3 response
- Click **Send**
- Expected result: JSON showing processing completed

#### 5. Upload Output to Anaplan
- Click on **"5. Upload Output to Anaplan (Export)"**
- Under **Body** tab, "form-data", key="file"
- Change to **"File"** type
- Select your processed Excel file
- Click **Send**
- Expected result: JSON showing "success": true
- Check: The file is now saved in `output_to_anaplan` folder

#### 6. Download File from Anaplan
- Click on **"6. Download File from Anaplan (Export)"**
- In the URL, replace the filename with your actual exported file name
- Click **Send**
- Expected result: File downloads to your computer

#### 7. List Exported Files
- Click on **"7. List Exported Files (Output)"**
- Click **Send**
- Expected result: JSON list of all exported files

#### 8. View Logs
- Click on **"8. View Server Logs"**
- Click **Send**
- Expected result: JSON showing all server activities

---

## Complete End-to-End Workflow

### Scenario: You want to simulate the full Anaplan integration

**Method 1: Using Python Scripts Only**
```bash
# Terminal 1: Start server
python server.py

# Terminal 2: Import data
python import_from_anaplan.py

# Terminal 3: Export processed data
python export_to_anaplan.py
```

**Method 2: Using Postman + Server**
```
1. Start server.py (Terminal 1)
2. Open Postman
3. Run "Health Check" to verify
4. Run "Import from Anaplan" with your Excel file
5. Run "List Imported Files" to verify
6. Run "Upload Output to Anaplan" with processed file
7. Run "List Exported Files" to verify
8. Run "Download File" to get the final output
```

**Method 3: Mixed (Recommended for Learning)**
```
1. Start server.py
2. Use Postman to import a file (Step 2)
3. Use Python script to process and export:
   python export_to_anaplan.py
4. Use Postman to download the file (Step 6)
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Run `pip install -r requirements.txt` again

### Problem: "Address already in use" when starting server
**Solution:** Another program is using port 5000. Either:
- Close the other program, or
- Change port in `server.py` (last line: `app.run(host='0.0.0.0', port=5001)`)

### Problem: Postman shows "Could not send request"
**Solution:** 
- Make sure server.py is running
- Check the URL is exactly `http://localhost:5000`
- Check Windows Firewall is not blocking Python

### Problem: "No file part in the request" in Postman
**Solution:**
- In Postman Body tab, select "form-data"
- Key must be exactly `file` (lowercase)
- Value type must be "File" not "Text"

### Problem: Cannot find imported/exported files
**Solution:**
- Check the folders: `input_from_anaplan` and `output_to_anaplan`
- Files are saved with timestamps, e.g., `20260101_120000_filename.xlsx`

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Check server status |
| `/api/import` | POST | Upload file (import from Anaplan) |
| `/api/files/input` | GET | List imported files |
| `/api/process/<file>` | POST | Process/transform a file |
| `/api/export/upload` | POST | Upload file (export to Anaplan) |
| `/api/export/<file>` | GET | Download file |
| `/api/files/output` | GET | List exported files |
| `/api/logs` | GET | View server logs |

---

## Next Steps / Customization

1. **Add your own data:** Replace the sample data in `import_from_anaplan.py` with your real Excel files
2. **Custom processing:** Edit `process_data_for_export()` in `export_to_anaplan.py` to add your business logic
3. **Authentication:** Add API keys to `server.py` for security
4. **Database:** Replace file storage with a real database
5. **Scheduling:** Use Windows Task Scheduler to run import/export scripts automatically

---

## Support

If you encounter issues:
1. Check the server logs: `GET http://localhost:5000/api/logs`
2. Check the terminal where server.py is running for error messages
3. Verify all files are in the correct folders
4. Make sure Python and all packages are installed correctly

Happy integrating!
