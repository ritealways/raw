"""
test_client.py - VS Code script to test the Mock Anaplan Server
Run this in VS Code to test the full pipeline without Postman.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

# Color codes for pretty printing
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_section(title):
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_json(data, title="Response"):
    print(f"\n{BOLD}{title}:{RESET}")
    print(json.dumps(data, indent=2))

# =============================================================================
# SAMPLE INPUT DATA (From your image)
# =============================================================================

SAMPLE_INPUT_DATA = [
    {
        "Month": "2022-01-01",
        "Region": "North East",
        "Channel": "Agency",
        "Industry_Class": "Agriculture",
        "Account_Size": "Small",
        "Payroll": 54915332.36,
        "Employee_Count": 1434,
        "Avg_Wage": 47941.17,
        "Payroll_Growth_Rate_YoY": 0.0,
        "Payroll_Growth_Rate_QoQ": 0.0,
        "Hazard_Group": 4,
        "Historical_Loss_Ratio": 0.798,
        "Claim_Frequency": 0.0,
        "Claim_Severity": 31605,
        "Loss_Development_Factor": 1.096,
        "Medical_Inflation_Index": 1.055,
        "Wage_Inflation_Index": 1.03,
        "Employer_Tenure": 5.016,
        "Exposure_Volatility_Score": 0.9302,
        "Filed_Rate_Change": 0.042,
        "Net_Rate_Achievement": 0.036,
        "Schedule_Rating_Factor": 0.9747,
        "Deductible_Level": 0,
        "Renewal_Uplift": 0.063,
        "Loss_Sensitive_Indicator": 0,
        "Policy_Limit_Change": 1,
        "Code_Reclassification_Frequ": 0,
        "Multi_Policy_Bundle_Indicator": 0.39,
        "Retention_Rate": 0.771,
        "Churn_Probability": 0.229,
        "New_Business_Hit_Ratio": 0.276,
        "Submission_to_Bind_Ratio": 0.175,
        "Policy_Term_Length": 12,
        "Endorsement_Frequency": 1,
        "Broker_Concentration": 0.046,
        "Seasonality_Index": -0.5,
        "Economic_Indicator": 0.65,
        "Employment_Growth_Rate": 0.12,
        "GWP": 856055.57
    },
    {
        "Month": "2022-02-01",
        "Region": "North East",
        "Channel": "Agency",
        "Industry_Class": "Agriculture",
        "Account_Size": "Small",
        "Payroll": 56315326.01,
        "Employee_Count": 1357,
        "Avg_Wage": 48368.42,
        "Payroll_Growth_Rate_YoY": 0.03,
        "Payroll_Growth_Rate_QoQ": 0.03,
        "Hazard_Group": 4,
        "Historical_Loss_Ratio": 0.841,
        "Claim_Frequency": 0.0,
        "Claim_Severity": 26910,
        "Loss_Development_Factor": 1.0704,
        "Medical_Inflation_Index": 1.0611,
        "Wage_Inflation_Index": 1.0355,
        "Employer_Tenure": 5.1238,
        "Exposure_Volatility_Score": 2.1805,
        "Filed_Rate_Change": 0.041,
        "Net_Rate_Achievement": 0.038,
        "Schedule_Rating_Factor": 1.1174,
        "Deductible_Level": 0,
        "Renewal_Uplift": 0.07,
        "Loss_Sensitive_Indicator": 0,
        "Policy_Limit_Change": 0,
        "Code_Reclassification_Frequ": 0,
        "Multi_Policy_Bundle_Indicator": 0.27,
        "Retention_Rate": 0.786,
        "Churn_Probability": 0.215,
        "New_Business_Hit_Ratio": 0.185,
        "Submission_to_Bind_Ratio": 0.225,
        "Policy_Term_Length": 12,
        "Endorsement_Frequency": 3,
        "Broker_Concentration": 0.011,
        "Seasonality_Index": -0.3464,
        "Economic_Indicator": 0.6298,
        "Employment_Growth_Rate": 0.008,
        "GWP": 971752.92
    },
    {
        "Month": "2022-03-01",
        "Region": "North East",
        "Channel": "Agency",
        "Industry_Class": "Agriculture",
        "Account_Size": "Small",
        "Payroll": 53848555.91,
        "Employee_Count": 1418,
        "Avg_Wage": 43440.05,
        "Payroll_Growth_Rate_YoY": 0.08,
        "Payroll_Growth_Rate_QoQ": 0.02,
        "Hazard_Group": 4,
        "Historical_Loss_Ratio": 0.758,
        "Claim_Frequency": 0.0,
        "Claim_Severity": 27747,
        "Loss_Development_Factor": 1.0593,
        "Medical_Inflation_Index": 1.066,
        "Wage_Inflation_Index": 1.0413,
        "Employer_Tenure": 5.1777,
        "Exposure_Volatility_Score": 1.5353,
        "Filed_Rate_Change": 0.041,
        "Net_Rate_Achievement": 0.04,
        "Schedule_Rating_Factor": 1.0064,
        "Deductible_Level": 0,
        "Renewal_Uplift": 0.079,
        "Loss_Sensitive_Indicator": 0,
        "Policy_Limit_Change": -1,
        "Code_Reclassification_Frequ": 0,
        "Multi_Policy_Bundle_Indicator": 0.22,
        "Retention_Rate": 0.823,
        "Churn_Probability": 0.177,
        "New_Business_Hit_Ratio": 0.05,
        "Submission_to_Bind_Ratio": 0.585,
        "Policy_Term_Length": 12,
        "Endorsement_Frequency": 0,
        "Broker_Concentration": 0.05,
        "Seasonality_Index": -0.1634,
        "Economic_Indicator": 0.6144,
        "Employment_Growth_Rate": 0.015,
        "GWP": 1120470.33
    }
]

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_health():
    """Step 1: Check if server is running."""
    print_section("STEP 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is healthy and running!")
            print_json(response.json(), "Health Response")
            return True
        else:
            print_error(f"Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on localhost:5000?")
        print_info("Run: python server.py  (in another terminal)")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_upload_input():
    """Step 2: Upload input data to mock Anaplan."""
    print_section("STEP 2: Upload Input Data to Mock Anaplan")

    try:
        response = requests.post(
            f"{BASE_URL}/api/anaplan/upload-input",
            json={"data": SAMPLE_INPUT_DATA},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Uploaded {data['records_uploaded']} records successfully!")
            print_json(data, "Upload Response")
            return True
        else:
            print_error(f"Upload failed with status {response.status_code}")
            print_json(response.json(), "Error Response")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_run_forecast():
    """Step 3: Run the wc_lightgbm forecasting model."""
    print_section("STEP 3: Run wc_lightgbm Forecast Model")

    try:
        response = requests.post(
            f"{BASE_URL}/api/anaplan/run-forecast",
            json={},  # Uses stored data
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Forecast generated successfully!")
            print_json(data, "Forecast Response")

            # Pretty print the forecast table
            print(f"\n{BOLD}Forecast Results Table:{RESET}")
            print("-" * 80)
            print(f"{'Month':<12} {'Region':<12} {'Channel':<10} {'Industry':<12} {'Size':<8} {'P10':>12} {'P50':>12} {'P90':>12}")
            print("-" * 80)
            for record in data['forecast']:
                print(f"{record['Month']:<12} {record['Region']:<12} {record['Channel']:<10} "
                      f"{record['Industry_Class']:<12} {record['Account_Size']:<8} "
                      f"${record['P10']:>10,.0f} ${record['P50']:>10,.0f} ${record['P90']:>10,.0f}")
            print("-" * 80)
            return True
        else:
            print_error(f"Forecast failed with status {response.status_code}")
            print_json(response.json(), "Error Response")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_get_forecast():
    """Step 4: Retrieve forecast output."""
    print_section("STEP 4: Get Forecast Output")

    try:
        response = requests.get(f"{BASE_URL}/api/anaplan/forecast-output", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data['record_count']} forecast records!")
            print_json(data, "Forecast Output")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_push_output():
    """Step 5: Push forecast output to Anaplan module."""
    print_section("STEP 5: Push Output to Anaplan Module")

    try:
        response = requests.post(
            f"{BASE_URL}/api/anaplan/push-output",
            json={"target_module": "WC_Forecast_Module"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Pushed {data['records_pushed']} records to '{data['target_module']}'!")
            print_json(data, "Push Response")
            return True
        else:
            print_error(f"Push failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_full_pipeline():
    """Run the complete end-to-end pipeline."""
    print(f"\n{BOLD}{'#'*70}{RESET}")
    print(f"{BOLD}{'#'*20}  FULL PIPELINE TEST  {'#'*20}{RESET}")
    print(f"{BOLD}{'#'*70}{RESET}")

    steps = [
        ("Health Check", test_health),
        ("Upload Input", test_upload_input),
        ("Run Forecast", test_run_forecast),
        ("Get Forecast", test_get_forecast),
        ("Push Output", test_push_output)
    ]

    results = []
    for name, func in steps:
        success = func()
        results.append((name, success))
        if not success:
            print_warning(f"Pipeline stopped at: {name}")
            break

    # Summary
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  PIPELINE SUMMARY{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    for name, success in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {name:<20} → {status}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print(f"\n{BOLD}{GREEN}🎉 All pipeline steps completed successfully!{RESET}")
    else:
        print(f"\n{BOLD}{RED}⚠️  Some pipeline steps failed. Check errors above.{RESET}")

# =============================================================================
# MENU
# =============================================================================

def show_menu():
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  MOCK ANAPLAN SERVER - VS CODE TEST CLIENT{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    print("""
    Choose an option:

    1. Run FULL Pipeline (Health → Upload → Forecast → Get → Push)
    2. Test Health Check only
    3. Test Upload Input only
    4. Test Run Forecast only
    5. Test Get Forecast only
    6. Test Push Output only
    7. Exit
    """)

if __name__ == '__main__':
    import sys

    # If arguments provided, run specific test
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['full', 'all', '1']:
            test_full_pipeline()
        elif arg in ['health', '2']:
            test_health()
        elif arg in ['upload', '3']:
            test_upload_input()
        elif arg in ['forecast', '4']:
            test_run_forecast()
        elif arg in ['get', '5']:
            test_get_forecast()
        elif arg in ['push', '6']:
            test_push_output()
        else:
            print("Usage: python test_client.py [full|health|upload|forecast|get|push]")
    else:
        # Interactive menu
        while True:
            show_menu()
            choice = input("Enter your choice (1-7): ").strip()

            if choice == '1':
                test_full_pipeline()
            elif choice == '2':
                test_health()
            elif choice == '3':
                test_upload_input()
            elif choice == '4':
                test_run_forecast()
            elif choice == '5':
                test_get_forecast()
            elif choice == '6':
                test_push_output()
            elif choice == '7':
                print("Goodbye!")
                break
            else:
                print_error("Invalid choice. Please enter 1-7.")
