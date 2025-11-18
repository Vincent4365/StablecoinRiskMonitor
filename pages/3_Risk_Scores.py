import streamlit as st
import plotly.express as px
from utils.load_data import load_demo_data

st.title("Risk Scores")

df = load_demo_data()

st.write(
    "This page uses a simple public risk model."
)

tokens = st.multiselect(
    "Filter by token",
    sorted(df["token"].unique()),
    default=sorted(df["token"].unique()),
)

filtered = df[df["token"].isin(tokens)]

st.subheader("Public risk score distribution")

fig_hist = px.histogram(
    filtered,
    x="risk_score_public",
    nbins=10,
    color="token",
    barmode="overlay",
    opacity=0.7,
    labels={"risk_score_public": "Public risk score"},
)
st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Average component scores by token")
comp = (
    filtered.groupby("token", as_index=False)[
        ["volume_score", "token_profile_score", "sanctions_score", "risk_score_public"]
    ].mean()
)
st.dataframe(comp)

st.subheader("Top high-risk wallets (public score)")

top_n = st.slider("Number of wallets to show", 5, 20, 10)

top_wallets = (
    filtered.sort_values("risk_score_public", ascending=False)
    .drop_duplicates("wallet_id")
    .head(top_n)
    [["wallet_id", "token", "tx_volume_usd", "risk_score_public"]]
)

st.dataframe(top_wallets)