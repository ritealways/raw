"""
Anaplan Workflow Orchestrator
Runs the complete flow: Server → Pull Data → Launch Streamlit → Push Output
"""
import subprocess
import time
import os
import sys
from pathlib import Path
import signal

# Configuration
SERVER_SCRIPT = "mock_anaplan_server.py"
STREAMLIT_APP = "app.py"  # YOUR existing Streamlit app
BRIDGE_SCRIPT = "anaplan_bridge.py"


def print_banner(text):
    """Print a fancy banner"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def start_anaplan_server():
    """Start the mock Anaplan server in background"""
    print_banner("🚀 Starting Mock Anaplan Server")

    # Check if already running
    try:
        import requests
        resp = requests.get("http://localhost:8000/", timeout=2)
        if resp.status_code == 200:
            print("   ✅ Server already running at http://localhost:8000")
            return None
    except:
        pass

    # Start server
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    print("   Waiting for server to start...")
    time.sleep(3)

    # Verify
    try:
        import requests
        resp = requests.get("http://localhost:8000/", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Server started successfully!")
            print("   📍 http://localhost:8000")
            print("   📖 http://localhost:8000/docs")
            return process
    except:
        pass

    print("   ⚠️ Server may not have started properly")
    return process


def pull_from_anaplan():
    """Pull data from Anaplan using bridge"""
    print_banner("📥 Pulling Data from Anaplan")

    result = subprocess.run(
        [sys.executable, BRIDGE_SCRIPT, "pull"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def launch_streamlit():
    """Launch your Streamlit app"""
    print_banner("🖥️  Launching Streamlit App")
    print("   Your app will open in browser shortly...")
    print("   \n   👉 IN YOUR APP:")
    print("      1. Load the file: bridge_data/temp_input_from_anaplan.csv")
    print("      2. Run your ML model")
    print("      3. Download the forecast output")
    print("      4. Come back here and press ENTER to continue\n")

    # Launch Streamlit
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", STREAMLIT_APP],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give it time to open browser
    time.sleep(5)

    # Wait for user
    input("\n🔄 Press ENTER after you've downloaded the output from Streamlit...")

    # Terminate streamlit
    process.terminate()
    try:
        process.wait(timeout=5)
    except:
        process.kill()

    return True


def push_to_anaplan(output_file: str = None):
    """Push output back to Anaplan"""
    print_banner("📤 Pushing Output to Anaplan")

    # Auto-detect output file if not specified
    if not output_file:
        # Look for recently downloaded files
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            csv_files = sorted(
                [f for f in downloads.glob("*.csv")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            if csv_files:
                output_file = str(csv_files[0])
                print(f"   Auto-detected latest CSV: {csv_files[0].name}")

    if not output_file or not os.path.exists(output_file):
        output_file = input("\n📁 Enter path to your output CSV file: ").strip().strip('"')

    if not os.path.exists(output_file):
        print(f"   ❌ File not found: {output_file}")
        return False

    result = subprocess.run(
        [sys.executable, BRIDGE_SCRIPT, "push", output_file],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def run_full_workflow():
    """Run the complete end-to-end workflow"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🌐 ANAPLAN INTEGRATION WORKFLOW ORCHESTRATOR             ║
║                                                              ║
║     This will:                                               ║
║     1. Start the Mock Anaplan Server                         ║
║     2. Pull input data from "Anaplan"                        ║
║     3. Launch your Streamlit app                             ║
║     4. Push forecast output back to "Anaplan"                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Step 1: Start server
    server_process = start_anaplan_server()

    # Step 2: Pull data (only if data exists on server)
    print("\n   Do you want to pull data from Anaplan? (y/n): ", end="")
    if input().lower() == 'y':
        pull_from_anaplan()

    # Step 3: Launch Streamlit
    print("\n   Ready to launch Streamlit app? (y/n): ", end="")
    if input().lower() == 'y':
        launch_streamlit()

    # Step 4: Push output
    print("\n   Ready to push output to Anaplan? (y/n): ", end="")
    if input().lower() == 'y':
        push_to_anaplan()

    print_banner("✅ WORKFLOW COMPLETE")
    print("   Check http://localhost:8000/docs for API details")

    if server_process:
        print("\n   Keep server running? (y/n): ", end="")
        if input().lower() != 'y':
            server_process.terminate()
            print("   Server stopped.")


def run_server_only():
    """Just start the server"""
    server_process = start_anaplan_server()
    if server_process:
        print("\n   Server is running. Press CTRL+C to stop.")
        try:
            server_process.wait()
        except KeyboardInterrupt:
            server_process.terminate()
            print("\n   Server stopped.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server_only()
    else:
        run_full_workflow()
