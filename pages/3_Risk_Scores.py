import streamlit as st
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
    sorted(df["Token"].unique()),
    default=sorted(df["Token"].unique()),
)

filtered = df[df["Token"].isin(tokens)]

st.subheader("Public risk score distribution")

fig_hist = px.histogram(
    filtered,
    x="Risk Score",
    nbins=30,  # smoother shape
    color="Token",
    barmode="overlay",
    opacity=0.6,
    labels={"Risk Score": "Public risk score"},
)
st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Average component scores by token")

comp = (
    filtered.groupby("Token", as_index=False)[
        [
            "Volume Score",
            "Token Score",
            "Concentration Score",
            "Velocity Score",
            "Sanctions Score",
            "Risk Score",
        ]
    ].mean()
)

st.dataframe(comp)

st.subheader("Top high-risk wallets (by public score)")

top_n = st.slider("Number of wallets to show", 5, 20, 10)

top_wallets = (
    filtered.sort_values("Risk Score", ascending=False)
    .drop_duplicates("Wallet")
    .head(top_n)[
        ["Wallet", "Token", "Volume", "Risk Score"]
    ]
)

st.dataframe(top_wallets)