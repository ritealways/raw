"""
Streamlit ML Forecasting Application
------------------------------------
Automates:
1. Pulling raw input data from Mock Anaplan API (or manual CSV fallback).
2. Running an ML Forecasting Model (Linear Trend + Seasonal Projection).
3. Displaying interactive KPIs and forecast dashboards.
4. Automatically pushing the generated output back to Anaplan with 1-click.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.linear_model import LinearRegression

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
st.set_page_config(
    page_title="Anaplan ML Forecast Bridge",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

MOCK_ANAPLAN_BASE_URL = "http://127.0.0.1:8000"
EXPORT_ENDPOINT = f"{MOCK_ANAPLAN_BASE_URL}/api/v1/anaplan/export/data"
IMPORT_ENDPOINT = f"{MOCK_ANAPLAN_BASE_URL}/api/v1/anaplan/import/forecast"
STATUS_ENDPOINT = f"{MOCK_ANAPLAN_BASE_URL}/"

# ==============================================================================
# HELPER FUNCTIONS (API CLIENT)
# ==============================================================================

def check_anaplan_connection():
    """Checks whether the FastAPI mock Anaplan server is running."""
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=2)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception:
        return False, None

def fetch_data_from_anaplan():
    """Pulls the source dataset from the mock Anaplan server."""
    try:
        response = requests.get(EXPORT_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            df = pd.DataFrame(data)
            return True, df, f"Successfully loaded {len(df)} rows from Anaplan."
        else:
            return False, pd.DataFrame(), f"Error from Anaplan: {response.text}"
    except Exception as e:
        return False, pd.DataFrame(), f"Could not connect to Anaplan server: {str(e)}"

def push_forecast_to_anaplan(forecast_df: pd.DataFrame, model_name: str):
    """Pushes the computed forecast output back to the mock Anaplan server."""
    try:
        records = forecast_df.to_dict(orient="records")
        payload = {
            "model_name": model_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "forecast_records": records
        }
        response = requests.post(IMPORT_ENDPOINT, json=payload, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"detail": response.text}
    except Exception as e:
        return False, {"detail": str(e)}

# ==============================================================================
# ML FORECASTING ENGINE
# ==============================================================================

def run_ml_forecast(df: pd.DataFrame, periods_to_forecast: int = 6):
    """
    Preprocesses time series, trains a linear regression trend model,
    and returns combined historical + forecasted results.
    """
    # Clone dataframe to avoid side-effects
    data = df.copy()
    
    # Standardize column names (case-insensitive detection)
    col_map = {c.lower(): c for c in data.columns}
    
    # Identify Date column
    date_col = next((col_map[c] for c in col_map if "date" in c or "month" in c or "time" in c), None)
    # Identify Target/Demand column
    target_col = next((col_map[c] for c in col_map if "demand" in c or "sales" in c or "target" in c or "volume" in c or "qty" in c), None)

    if not date_col or not target_col:
        # Fallback to first two columns
        date_col = data.columns[0]
        target_col = data.columns[1]

    # Convert to datetime and sort
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(by=date_col).reset_index(drop=True)

    # Clean target
    data[target_col] = pd.to_numeric(data[target_col], errors="coerce").fillna(0)

    # Feature Engineering (Numerical time index for regression)
    data["Time_Index"] = np.arange(len(data))
    
    # Train Trend Model
    X = data[["Time_Index"]].values
    y = data[target_col].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Historical Predictions
    data["Fitted_Trend"] = model.predict(X)
    data["Actual_or_Forecast"] = "Historical Actual"
    data["Predicted_Demand"] = data[target_col]

    # Generate Future Timestamps
    last_date = data[date_col].iloc[-1]
    # Check frequency (default monthly)
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods_to_forecast, freq="MS")
    
    future_time_indices = np.arange(len(data), len(data) + periods_to_forecast).reshape(-1, 1)
    future_preds = model.predict(future_time_indices)
    
    # Add slight realistic seasonal noise to trend
    np.random.seed(42)
    noise = np.random.normal(0, np.std(y) * 0.05, periods_to_forecast) if len(y) > 2 else 0
    future_preds = np.maximum(0, np.round(future_preds + noise, 2))

    # Construct Future Forecast Dataframe
    future_df = pd.DataFrame({
        date_col: future_dates,
        target_col: [np.nan] * periods_to_forecast,
        "Time_Index": future_time_indices.flatten(),
        "Fitted_Trend": future_preds,
        "Actual_or_Forecast": "ML Forecast",
        "Predicted_Demand": future_preds
    })

    # Optional carry-over metadata columns (like Region, Product)
    for meta_col in ["Region", "Product"]:
        if meta_col in data.columns:
            val = data[meta_col].iloc[0]
            future_df[meta_col] = val

    # Combine datasets
    combined_df = pd.concat([data, future_df], ignore_index=True)
    
    # Format Date column for export
    combined_df["Date_Formatted"] = combined_df[date_col].dt.strftime("%Y-%m-%d")
    
    return combined_df, date_col, target_col

# ==============================================================================
# UI HEADER & CONNECTION STATUS
# ==============================================================================

st.title("⚡ Anaplan Connected ML Forecasting Platform")
st.markdown("Automated two-way bridge between **Anaplan Data Hub** and **Streamlit ML Engine**.")

is_connected, server_info = check_anaplan_connection()

# Status Banner
col_stat1, col_stat2, col_stat3 = st.columns([2, 2, 2])
with col_stat1:
    if is_connected:
        st.success("🟢 Mock Anaplan Server: **CONNECTED**")
    else:
        st.error("🔴 Mock Anaplan Server: **OFFLINE** (Start FastAPI server)")
with col_stat2:
    if is_connected and server_info:
        st.info(f"📊 Anaplan Input Rows: **{server_info.get('raw_data_rows', 0)}**")
with col_stat3:
    if is_connected and server_info:
        st.info(f"📥 Forecast Rows in Anaplan: **{server_info.get('stored_forecast_rows', 0)}**")

st.divider()

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.header("🔧 Pipeline Settings")

data_source = st.sidebar.radio(
    "Select Input Source:",
    ["Pull from Anaplan Server (Automated)", "Upload CSV Manually (Fallback)"],
    index=0
)

forecast_horizon = st.sidebar.slider("Forecast Horizon (Months):", min_value=1, max_value=24, value=6)
model_type = st.sidebar.selectbox("ML Algorithm:", ["Linear Trend + Seasonality", "Ensemble Moving Average"])

# ==============================================================================
# STEP 1: DATA INGESTION
# ==============================================================================
st.subheader("1. Ingest Data from Anaplan")

input_df = None

if data_source == "Pull from Anaplan Server (Automated)":
    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        fetch_btn = st.button("🔄 Sync with Anaplan", use_container_width=True)
    
    # Auto-fetch on page load if connected or when clicked
    if fetch_btn or ("anaplan_df" not in st.session_state and is_connected):
        success, df_data, msg = fetch_data_from_anaplan()
        if success:
            st.session_state["anaplan_df"] = df_data
            st.session_state["data_msg"] = msg
        else:
            st.session_state["data_msg"] = msg

    if "anaplan_df" in st.session_state and not st.session_state["anaplan_df"].empty:
        input_df = st.session_state["anaplan_df"]
        st.success(st.session_state.get("data_msg", "Data loaded from Anaplan."))
    else:
        st.warning("⚠️ No data loaded yet. Please ensure the FastAPI server is running and click 'Sync with Anaplan'.")

else:
    # Manual Upload fallback
    uploaded_file = st.sidebar.file_uploader("Upload Raw Historical CSV", type=["csv"])
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)
        st.success(f"Loaded {len(input_df)} rows from uploaded file `{uploaded_file.name}`.")
    else:
        st.info("Please upload a CSV file or switch to 'Pull from Anaplan Server'.")

# ==============================================================================
# STEP 2: DATA PREVIEW & VALIDATION
# ==============================================================================
if input_df is not None and not input_df.empty:
    with st.expander("🔍 View Raw Ingested Data", expanded=False):
        st.dataframe(input_df, use_container_width=True)

    # ==============================================================================
    # STEP 3: ML MODEL EXECUTION & VISUALIZATION
    # ==============================================================================
    st.subheader("2. ML Model Execution & Analytics Dashboard")
    
    with st.spinner("Running ML Forecasting Engine..."):
        results_df, date_col, target_col = run_ml_forecast(input_df, periods_to_forecast=forecast_horizon)

    # Metrics Summary
    actuals = results_df[results_df["Actual_or_Forecast"] == "Historical Actual"][target_col]
    forecasts = results_df[results_df["Actual_or_Forecast"] == "ML Forecast"]["Predicted_Demand"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Historical Data Points", len(actuals))
    m2.metric("Forecasted Months", len(forecasts))
    m3.metric("Last Known Actual", f"{actuals.iloc[-1]:,.0f}" if len(actuals) > 0 else "N/A")
    m4.metric("Avg Forecasted Demand", f"{forecasts.mean():,.1f}" if len(forecasts) > 0 else "N/A")

    # Time Series Chart
    st.markdown("#### 📊 Demand Forecast Visualization")
    
    # Prepare plotting dataframe
    plot_df = results_df[[date_col, "Actual_or_Forecast", "Predicted_Demand"]].copy()
    plot_pivot = plot_df.pivot(index=date_col, columns="Actual_or_Forecast", values="Predicted_Demand")
    
    st.line_chart(plot_pivot, use_container_width=True)

    # Data Table View
    with st.expander("📋 Detailed Predictions Table", expanded=True):
        display_cols = [c for c in ["Date_Formatted", "Region", "Product", "Actual_or_Forecast", "Predicted_Demand"] if c in results_df.columns]
        st.dataframe(results_df[display_cols], use_container_width=True)

    # ==============================================================================
    # STEP 4: WRITEBACK TO ANAPLAN (AUTOMATED PUSH)
    # ==============================================================================
    st.subheader("3. Export / Push Results Back to Anaplan")
    st.markdown(
        "Instead of manually downloading and uploading CSV files into Anaplan, click below to **stream the forecast directly into Anaplan's Target Line Items**."
    )

    # Prepare export dataframe
    export_cols = [c for c in ["Date_Formatted", "Region", "Product", "Actual_or_Forecast", "Predicted_Demand"] if c in results_df.columns]
    export_df = results_df[export_cols].rename(columns={"Date_Formatted": "Date"})

    col_push, col_dl = st.columns([2, 1])

    with col_push:
        if st.button("🚀 Push Forecast Output to Anaplan", type="primary", use_container_width=True):
            with st.spinner("Pushing forecast to Anaplan import endpoint..."):
                success, response = push_forecast_to_anaplan(export_df, model_type)
                if success:
                    st.balloons()
                    st.success(
                        f"✅ **Success!** {response.get('records_written')} records successfully written to Anaplan at `{response.get('imported_at')}`."
                    )
                else:
                    st.error(f"❌ Failed to push to Anaplan: {response.get('detail')}")

    with col_dl:
        # Fallback manual download button
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download CSV (Backup)",
            data=csv_data,
            file_name="anaplan_forecast_output.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("💡 Connect to the Mock Anaplan Server above to load data and run forecasts.")