import streamlit as st
from utils.generate_demo_data import generate_demo_data
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

# Regenerate data button
if st.button("Regenerate Demo Dataset"):
    generate_demo_data()
    st.success("Demo dataset has been regenerated.")

st.title("Overview")

df = load_demo_data()

st.subheader("Demo dataset")
st.dataframe(df)

st.subheader("Key figures")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total volume (USD)", f"${df['tx_volume_usd'].sum():,.0f}")
with col2:
    st.metric("Number of wallets", df["wallet_id"].nunique())
with col3:
    st.metric("Average public risk score", f"{df['risk_score_public'].mean():.1f}")

st.subheader("Stablecoin volume over time")

daily = df.groupby(["date", "token"], as_index=False)["tx_volume_usd"].sum()

fig_vol = px.line(
    daily,
    x="date",
    y="tx_volume_usd",
    color="token",
    markers=False,
)
st.plotly_chart(fig_vol, use_container_width=True)

st.subheader("Total volume by token")

vol_token = df.groupby("token", as_index=False)["tx_volume_usd"].sum()
fig_token = px.bar(
    vol_token,
    x="tx_volume_usd",
    y="token",
    orientation="h",
    text="tx_volume_usd",
)

fig_token.update_traces(texttemplate="%{text:,.0f}")
st.plotly_chart(fig_token, use_container_width=True)
