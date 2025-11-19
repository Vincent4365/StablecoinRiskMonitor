import streamlit as st

if "data_source" not in st.session_state:
    st.session_state["data_source"] = "Demo Data"

import plotly.express as px
from utils.load_data import load_demo_data, load_real_data
from utils.sidebar import sidebar

# Shared sidebar
data_source = sidebar()

st.title("Risk Scores")

if data_source.startswith("Real"):
    df = load_real_data()
else:
    df = load_demo_data()

st.write(
    "This page shows the public risk score (0–100) and its main components: "
    "transaction volume, token profile, wallet concentration, activity, and sanctions intensity."
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
    nbins=30,  # smoother shape
    color="token",
    barmode="overlay",
    opacity=0.6,
    labels={"risk_score_public": "Public risk score"},
)
st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Average component scores by token")

comp = (
    filtered.groupby("token", as_index=False)[
        [
            "volume_score",
            "token_profile_score",
            "concentration_score",
            "velocity_score",
            "sanctions_score",
            "risk_score_public",
        ]
    ].mean()
)

st.dataframe(comp)

st.subheader("Top high-risk wallets (by public score)")

top_n = st.slider("Number of wallets to show", 5, 20, 10)

top_wallets = (
    filtered.sort_values("risk_score_public", ascending=False)
    .drop_duplicates("wallet_id")
    .head(top_n)[
        ["wallet_id", "token", "tx_volume_usd", "risk_score_public"]
    ]
)

st.dataframe(top_wallets)