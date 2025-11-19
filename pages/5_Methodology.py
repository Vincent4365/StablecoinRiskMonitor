import streamlit as st
from utils.sidebar import sidebar

# Shared sidebar
data_source = sidebar()

st.title("Methodology")

st.write(
    """
This page explains the methodology behind the risk scores and data sources used in this dashboard.
"""
)