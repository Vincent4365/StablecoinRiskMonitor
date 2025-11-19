import streamlit as st
from utils.sidebar import sidebar

# Shared sidebar
data_source = sidebar()

st.title("Methodology")

st.write(
    """
This page explains the methodology behind the risk scores and data sources 
used in this dashboard.

The public risk score combines several components:
- **Transaction volume** (size and frequency of transfers)
- **Token profile** (stablecoin type and contract characteristics)
- **Wallet concentration** (how volume is distributed across wallets)
- **Velocity/activity** (how quickly funds move through the wallet)
- **Sanctions intensity** (share of flows linked to flagged activity)

All blockchain addresses are fully anonymized before analysis, and no
personally identifiable wallet information is retained.
"""
)