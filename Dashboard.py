import streamlit as st
from utils.load_data import load_demo_data
import plotly.express as px

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

st.title("Overview")

df = load_demo_data()

st.subheader("Demo dataset")
st.dataframe(df)

st.subheader("Basic stats")
st.write(df.describe())

st.subheader("Volume over time")
fig = px.line(df, x="date", y="tx_volume_usd", color="token")
st.plotly_chart(fig, use_container_width=True)