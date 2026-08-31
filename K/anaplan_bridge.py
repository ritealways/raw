"""
Anaplan Bridge - Connects your Streamlit app to Mock Anaplan Server
This script acts as the middleman - no changes needed to your app.py
"""
import requests
import pandas as pd
import os
import json
from pathlib import Path
from datetime import datetime

# Configuration
ANAPLAN_SERVER_URL = "http://localhost:8000"
BRIDGE_DIR = Path("bridge_data")
BRIDGE_DIR.mkdir(exist_ok=True)

# Temporary files for data exchange
INPUT_TEMP = BRIDGE_DIR / "temp_input_from_anaplan.csv"
OUTPUT_TEMP = BRIDGE_DIR / "temp_output_for_anaplan.csv"
JOB_FILE = BRIDGE_DIR / "current_job.json"


def get_server_status():
    """Check if Anaplan server is running"""
    try:
        response = requests.get(f"{ANAPLAN_SERVER_URL}/", timeout=5)
        return response.json()
    except:
        return None


def create_job():
    """Create a new job on Anaplan server"""
    # First upload a placeholder to create job
    # In real flow, you'd upload actual data
    print("Creating new Anaplan job...")
    # Return a job ID format that the server expects
    return None


def pull_data_from_anaplan(job_id: str = None):
    """
    STEP 1: Pull input data from Anaplan server
    This downloads the CSV that was uploaded to Anaplan
    Returns: path to downloaded CSV file
    """
    print("\n" + "=" * 50)
    print("📥 STEP 1: Pulling data from Anaplan...")
    print("=" * 50)

    # If no job_id provided, check for latest available job
    if not job_id:
        try:
            resp = requests.get(f"{ANAPLAN_SERVER_URL}/api/v1/jobs", timeout=10)
            jobs = resp.json().get("jobs", [])
            ready_jobs = [j for j in jobs if j["status"] in ["ready", "pending"]]
            if ready_jobs:
                job_id = ready_jobs[-1]["job_id"]  # Get most recent ready job
                print(f"   Found job: {job_id}")
            else:
                print("   ⚠️ No ready jobs found on Anaplan server")
                return None
        except Exception as e:
            print(f"   ❌ Error checking jobs: {e}")
            return None

    # Download the input file
    try:
        print(f"   Downloading input file for job {job_id}...")
        response = requests.get(
            f"{ANAPLAN_SERVER_URL}/api/v1/download/{job_id}",
            timeout=30
        )

        if response.status_code == 200:
            # Save to temp location
            with open(INPUT_TEMP, "wb") as f:
                f.write(response.content)

            # Save job info
            with open(JOB_FILE, "w") as f:
                json.dump({"job_id": job_id, "timestamp": datetime.now().isoformat()}, f)

            print(f"   ✅ Data saved to: {INPUT_TEMP}")
            print(f"   📊 File size: {len(response.content)} bytes")
            return str(INPUT_TEMP)
        else:
            print(f"   ❌ Download failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ Error downloading: {e}")
        return None


def push_data_to_anaplan(output_file_path: str, metadata: dict = None):
    """
    STEP 2: Push forecast output back to Anaplan
    Uploads the generated output CSV to Anaplan server
    """
    print("\n" + "=" * 50)
    print("📤 STEP 2: Pushing output to Anaplan...")
    print("=" * 50)

    # Read current job info
    if not JOB_FILE.exists():
        print("   ❌ No active job found. Run pull_data_from_anaplan first.")
        return False

    with open(JOB_FILE, "r") as f:
        job_info = json.load(f)

    job_id = job_info.get("job_id")

    if not os.path.exists(output_file_path):
        print(f"   ❌ Output file not found: {output_file_path}")
        return False

    try:
        print(f"   Uploading {os.path.basename(output_file_path)} to job {job_id}...")

        with open(output_file_path, "rb") as f:
            files = {"file": (os.path.basename(output_file_path), f, "text/csv")}
            data = {"metadata": json.dumps(metadata) if metadata else "{}"}

            response = requests.post(
                f"{ANAPLAN_SERVER_URL}/api/v1/output/{job_id}",
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result['message']}")
            print(f"   📋 Job ID: {result['job_id']}")

            # Clean up job file
            JOB_FILE.unlink(missing_ok=True)
            return True
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error uploading: {e}")
        return False


def show_job_status(job_id: str = None):
    """Display current job status from Anaplan"""
    if not job_id and JOB_FILE.exists():
        with open(JOB_FILE, "r") as f:
            job_info = json.load(f)
        job_id = job_info.get("job_id")

    if not job_id:
        print("No active job")
        return

    try:
        resp = requests.get(f"{ANAPLAN_SERVER_URL}/api/v1/jobs/{job_id}", timeout=10)
        job = resp.json()
        print("\n📋 Job Status:")
        print(f"   ID: {job['job_id']}")
        print(f"   Status: {job['status']}")
        print(f"   Message: {job['message']}")
        print(f"   Input: {job.get('input_file', 'N/A')}")
        print(f"   Output: {job.get('output_file', 'N/A')}")
    except Exception as e:
        print(f"Error checking status: {e}")


def list_all_jobs():
    """List all jobs on Anaplan server"""
    try:
        resp = requests.get(f"{ANAPLAN_SERVER_URL}/api/v1/jobs", timeout=10)
        jobs = resp.json().get("jobs", [])
        print("\n📋 All Jobs on Anaplan Server:")
        print("-" * 60)
        for job in jobs:
            print(f"   {job['job_id']} | {job['status']:12} | {job.get('input_file', 'N/A')}")
    except Exception as e:
        print(f"Error listing jobs: {e}")


# ==================== COMMAND LINE INTERFACE ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║           ANAPLAN BRIDGE - Command Line Tool                 ║
╠══════════════════════════════════════════════════════════════╣
║  Usage:                                                      ║
║    python anaplan_bridge.py status        → Check server     ║
║    python anaplan_bridge.py pull          → Pull from server ║
║    python anaplan_bridge.py push <file>   → Push to server   ║
║    python anaplan_bridge.py jobs          → List all jobs    ║
╚══════════════════════════════════════════════════════════════╝
        """)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        status = get_server_status()
        if status:
            print("✅ Anaplan Server is RUNNING")
            print(f"   URL: {ANAPLAN_SERVER_URL}")
            print(f"   Service: {status['service']}")
        else:
            print("❌ Anaplan Server is NOT RUNNING")
            print("   Start it first: python mock_anaplan_server.py")

    elif cmd == "pull":
        job_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = pull_data_from_anaplan(job_id)
        if result:
            print(f"\n✅ Data ready at: {result}")
            print("   Now you can load this file in your Streamlit app!")
        else:
            print("\n❌ Failed to pull data")

    elif cmd == "push":
        if len(sys.argv) < 3:
            print("Usage: python anaplan_bridge.py push <output_file.csv>")
            sys.exit(1)
        output_path = sys.argv[2]
        success = push_data_to_anaplan(output_path)
        if success:
            print("\n✅ Output pushed to Anaplan successfully!")
        else:
            print("\n❌ Failed to push output")

    elif cmd == "jobs":
        list_all_jobs()

    else:
        print(f"Unknown command: {cmd}")
