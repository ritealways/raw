"""
standalone_forecast.py - Run wc_lightgbm directly without the server
Use this for quick testing or batch processing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

from wc_lightgbm import run_forecast
import json

# Input data from your image
INPUT_DATA = [
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

if __name__ == '__main__':
    print("=" * 70)
    print("  STANDALONE WC LIGHTGBM FORECAST")
    print("=" * 70)
    print("\nRunning forecast with 3 months of historical input data...\n")

    result = run_forecast(INPUT_DATA)

    print("\n" + "=" * 70)
    print("  FORECAST OUTPUT (Matches your image format)")
    print("=" * 70)

    for record in result:
        print(f"\n  Month: {record['Month']}")
        print(f"  Region: {record['Region']} | Channel: {record['Channel']}")
        print(f"  Industry: {record['Industry_Class']} | Size: {record['Account_Size']}")
        print(f"  P10 : ${record['P10']:,.2f}")
        print(f"  P50 : ${record['P50']:,.2f}")
        print(f"  P90 : ${record['P90']:,.2f}")
        print("  " + "-" * 50)

    # Save to JSON file
    output_file = 'forecast_output.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Forecast saved to: {output_file}")
