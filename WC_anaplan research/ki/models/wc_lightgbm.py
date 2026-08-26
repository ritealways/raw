"""
wc_lightgbm.py - Workers Compensation LightGBM Forecasting Model
This script takes input data (like from Anaplan) and generates P10/P50/P90 forecasts.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("Warning: LightGBM not installed. Using fallback RandomForest model.")

def parse_input_data(input_json):
    """
    Parse the input JSON data from Anaplan format.
    Expected format: List of monthly records with all features.
    """
    if isinstance(input_json, str):
        data = json.loads(input_json)
    else:
        data = input_json

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Ensure Month is datetime
    df['Month'] = pd.to_datetime(df['Month'])
    df = df.sort_values('Month').reset_index(drop=True)

    return df

def engineer_features(df):
    """
    Create features for the forecasting model.
    """
    df = df.copy()

    # Time-based features
    df['Month_Num'] = df['Month'].dt.month
    df['Year'] = df['Month'].dt.year
    df['Quarter'] = df['Month'].dt.quarter
    df['Month_Sin'] = np.sin(2 * np.pi * df['Month_Num'] / 12)
    df['Month_Cos'] = np.cos(2 * np.pi * df['Month_Num'] / 12)

    # Lag features (if we have enough history)
    if len(df) >= 3:
        df['Payroll_Lag1'] = df['Payroll'].shift(1)
        df['Payroll_Lag2'] = df['Payroll'].shift(2)
        df['GWP_Lag1'] = df['GWP'].shift(1)
        df['GWP_Lag2'] = df['GWP'].shift(2)
    else:
        df['Payroll_Lag1'] = df['Payroll']
        df['Payroll_Lag2'] = df['Payroll']
        df['GWP_Lag1'] = df['GWP']
        df['GWP_Lag2'] = df['GWP']

    # Rolling averages
    df['Payroll_MA3'] = df['Payroll'].rolling(window=3, min_periods=1).mean()
    df['GWP_MA3'] = df['GWP'].rolling(window=3, min_periods=1).mean()

    # Growth features
    df['Payroll_Growth'] = df['Payroll'].pct_change().fillna(0)
    df['Employee_Growth'] = df['Employee_Count'].pct_change().fillna(0)

    # Interaction features
    df['Payroll_per_Employee'] = df['Payroll'] / df['Employee_Count'].clip(lower=1)
    df['Loss_Ratio_x_Frequency'] = df['Historical_Loss_Ratio'] * df['Claim_Frequency']

    # Encode categorical features
    categorical_cols = ['Region', 'Channel', 'Industry_Class', 'Account_Size']
    for col in categorical_cols:
        if col in df.columns:
            df[col + '_Encoded'] = pd.Categorical(df[col]).codes

    # Fill any NaN values
    df = df.fillna(df.median(numeric_only=True))

    return df

def train_forecast_model(df, target_col='GWP', forecast_months=3):
    """
    Train a LightGBM model (or fallback) and generate P10/P50/P90 forecasts.
    """
    df = engineer_features(df)

    # Feature columns (exclude target and non-feature columns)
    exclude_cols = ['Month', 'GWP', 'Region', 'Channel', 'Industry_Class', 'Account_Size']
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    X = df[feature_cols].values
    y = df[target_col].values

    # Train model
    if LIGHTGBM_AVAILABLE:
        model = lgb.LGBMRegressor(
            objective='regression',
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
    else:
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)

    model.fit(X, y)

    # Generate predictions for historical data to calculate residuals
    historical_preds = model.predict(X)
    residuals = y - historical_preds
    residual_std = np.std(residuals)

    # Create future dates
    last_date = df['Month'].max()
    future_dates = [last_date + timedelta(days=30*i) for i in range(1, forecast_months + 1)]

    # Create future feature rows (using last known values with projections)
    future_rows = []
    last_row = df.iloc[-1].copy()

    for i, future_date in enumerate(future_dates):
        new_row = last_row.copy()
        new_row['Month'] = future_date
        new_row['Month_Num'] = future_date.month
        new_row['Year'] = future_date.year
        new_row['Quarter'] = (future_date.month - 1) // 3 + 1
        new_row['Month_Sin'] = np.sin(2 * np.pi * future_date.month / 12)
        new_row['Month_Cos'] = np.cos(2 * np.pi * future_date.month / 12)

        # Project payroll with growth
        payroll_growth = df['Payroll_Growth'].mean() if 'Payroll_Growth' in df.columns else 0.02
        new_row['Payroll'] = last_row['Payroll'] * (1 + payroll_growth)
        new_row['Payroll_Lag1'] = last_row['Payroll']
        new_row['Payroll_Lag2'] = df['Payroll'].iloc[-2] if len(df) > 1 else last_row['Payroll']
        new_row['Payroll_MA3'] = df['Payroll'].tail(3).mean()

        # Project GWP with slight growth
        gwp_growth = 0.03  # 3% assumed growth
        new_row['GWP'] = last_row['GWP'] * (1 + gwp_growth)
        new_row['GWP_Lag1'] = last_row['GWP']
        new_row['GWP_Lag2'] = df['GWP'].iloc[-2] if len(df) > 1 else last_row['GWP']
        new_row['GWP_MA3'] = df['GWP'].tail(3).mean()

        # Update employee count
        emp_growth = df['Employee_Growth'].mean() if 'Employee_Growth' in df.columns else 0.01
        new_row['Employee_Count'] = int(last_row['Employee_Count'] * (1 + emp_growth))

        new_row['Payroll_per_Employee'] = new_row['Payroll'] / max(new_row['Employee_Count'], 1)

        future_rows.append(new_row)
        last_row = new_row

    future_df = pd.DataFrame(future_rows)
    future_df = engineer_features(future_df)

    # Ensure same columns
    for col in feature_cols:
        if col not in future_df.columns:
            future_df[col] = 0

    X_future = future_df[feature_cols].values

    # Generate point predictions (P50)
    p50_preds = model.predict(X_future)

    # Generate P10 and P90 using residual distribution
    # P10 = prediction - 1.28 * std(residuals)
    # P90 = prediction + 1.28 * std(residuals)
    p10_preds = p50_preds - 1.28 * residual_std
    p90_preds = p50_preds + 1.28 * residual_std

    # Ensure positive values
    p10_preds = np.maximum(p10_preds, p50_preds * 0.5)
    p90_preds = np.maximum(p90_preds, p50_preds * 1.2)

    # Format results
    results = []
    for i, date in enumerate(future_dates):
        results.append({
            'Month': date.strftime('%b-%Y'),
            'Region': df['Region'].iloc[0],
            'Channel': df['Channel'].iloc[0],
            'Industry_Class': df['Industry_Class'].iloc[0],
            'Account_Size': df['Account_Size'].iloc[0],
            'P10': round(p10_preds[i], 2),
            'P50': round(p50_preds[i], 2),
            'P90': round(p90_preds[i], 2)
        })

    return results

def run_forecast(input_data):
    """
    Main entry point: takes input data, runs forecast, returns output.
    """
    df = parse_input_data(input_data)
    forecasts = train_forecast_model(df, forecast_months=3)
    return forecasts


# For direct testing
if __name__ == '__main__':
    # Sample test data matching the image
    test_input = [
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

    print("Running WC LightGBM Forecast Model...")
    print("=" * 60)

    result = run_forecast(test_input)

    print("\nForecast Output:")
    print("-" * 60)
    for r in result:
        print(f"Month: {r['Month']}")
        print(f"  Region: {r['Region']} | Channel: {r['Channel']} | Industry: {r['Industry_Class']} | Size: {r['Account_Size']}")
        print(f"  P10: ${r['P10']:,.2f}")
        print(f"  P50 (Median): ${r['P50']:,.2f}")
        print(f"  P90: ${r['P90']:,.2f}")
        print()
