"""
HOW TO WIRE THIS INTO YOUR EXISTING app.py
--------------------------------------------
You don't need to rewrite app.py. Just paste this snippet near the top
of your "Data" page / Data Input section (wherever the file-uploader
drag-and-drop box is), and add the two buttons shown below.

This does NOT replace your manual "Drag and drop" uploader — it just
adds an alternative "Pull from Anaplan" button next to it, and a
"Push results to Anaplan" button near your Results/Dashboard section.
"""

import streamlit as st
import pandas as pd
from anaplan_client import fetch_input_from_anaplan, push_output_to_anaplan, anaplan_status

# ---------------------------------------------------------------
# 1) PASTE THIS in your "Data Input" section (replaces/augments the
#    manual file uploader)
# ---------------------------------------------------------------
st.subheader("Data Input")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Drag and drop file here", type=["csv", "xlsx"])

with col2:
    if st.button("📥 Pull input from Anaplan"):
        try:
            local_path = fetch_input_from_anaplan(save_path="input.csv")
            st.success(f"Input pulled from Anaplan and saved as {local_path}")
            # Load it exactly the way your app already loads uploaded files
            df = pd.read_csv(local_path)
            st.session_state["input_df"] = df
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Failed to pull from Anaplan: {e}")

# ---------------------------------------------------------------
# 2) PASTE THIS wherever your app finishes generating output.csv
#    (usually right after your model/forecast step, near Results)
# ---------------------------------------------------------------
st.subheader("Push Results to Anaplan")

if st.button("📤 Push output to Anaplan"):
    try:
        # Change "output.csv" to whatever path your app already saves
        # the forecast results to.
        result = push_output_to_anaplan(local_file_path="output.csv")
        st.success(f"Output pushed to Anaplan successfully: {result}")
    except Exception as e:
        st.error(f"Failed to push to Anaplan: {e}")

# ---------------------------------------------------------------
# Optional: show a small status panel anywhere in your sidebar
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### Anaplan Connection")
    if st.button("Check Anaplan status"):
        try:
            st.json(anaplan_status())
        except Exception as e:
            st.error(f"Anaplan server not reachable: {e}")
