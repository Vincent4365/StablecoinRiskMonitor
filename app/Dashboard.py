import streamlit as st

st.set_page_config(
    page_title="Stablecoin Risk Monitor",
    page_icon="💱",
    layout="wide",
)

st.title("Stablecoin Risk Monitor")
st.write("Welcome to the public dashboard.")

st.markdown(
    """
This app is a prototype dashboard for monitoring stablecoin activity and AML-related risk signals.
"""
)