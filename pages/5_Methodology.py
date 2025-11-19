import streamlit as st
if "data_source" not in st.session_state:
    st.session_state["data_source"] = "Demo Data"
from utils.sidebar import sidebar

# Shared sidebar
data_source = sidebar()

st.title("Methodology")

st.write(
    """
This page explains the methodology behind the risk scores and data sources used in this dashboard.
"""
)