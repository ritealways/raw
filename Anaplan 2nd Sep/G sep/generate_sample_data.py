import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANAPLAN_INPUT_DIR = os.path.join(BASE_DIR, "anaplan_storage", "input_source")
LOCAL_OUTPUT_DIR = os.path.join(BASE_DIR, "local_storage", "processed_outputs")

os.makedirs(ANAPLAN_INPUT_DIR, exist_ok=True)
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)

# 1. Create mock input file in Anaplan
input_df = pd.DataFrame({
    "Account_ID": ["A1001", "A1002", "A1003", "A1004"],
    "Cost_Center": ["CC_HQ", "CC_OPS", "CC_FIN", "CC_TECH"],
    "Budget_Q1": [150000, 85000, 120000, 310000],
    "Currency": ["USD", "USD", "USD", "USD"]
})
input_path = os.path.join(ANAPLAN_INPUT_DIR, "sample_anaplan_input.xlsx")
input_df.to_excel(input_path, index=False)
print(f"Created mock input Excel: {input_path}")

# 2. Create mock processed output file locally
output_df = pd.DataFrame({
    "Account_ID": ["A1001", "A1002", "A1003", "A1004"],
    "Forecast_Q2": [165000, 91000, 128000, 335000],
    "Variance_Pct": [0.10, 0.07, 0.06, 0.08],
    "Status": ["Approved", "Approved", "Pending", "Approved"]
})
output_path = os.path.join(LOCAL_OUTPUT_DIR, "processed_output.xlsx")
output_df.to_excel(output_path, index=False)
print(f"Created mock processed Excel: {output_path}")
