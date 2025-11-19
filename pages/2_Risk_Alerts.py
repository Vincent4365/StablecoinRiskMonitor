import streamlit as st
import pandas as pd
from utils.load_data import load_demo_data, load_real_data
from utils.sidebar import sidebar

data_source = sidebar()

st.title("Top Flags")

if data_source.startswith("Real"):
    df = load_real_data()
else:
    df = load_demo_data()

if df.empty:
    st.info("No data available.")
    st.stop()

if "sanctions_flag" not in df.columns:
    df["sanctions_flag"] = 0

df["sanctions_flag"] = df["sanctions_flag"].astype(int)
df["sanctioned_volume"] = df["tx_volume_usd"] * df["sanctions_flag"]

# wallet-level aggregates
wallet_agg = (
    df.groupby("wallet_id", as_index=False)
    .agg(
        total_volume_usd=("tx_volume_usd", "sum"),
        n_transactions=("tx_volume_usd", "count"),
        avg_risk=("risk_score_public", "mean"),
        max_risk=("risk_score_public", "max"),
        sanctions_volume=("sanctioned_volume", "sum"),
    )
)

wallet_agg["has_sanctions"] = wallet_agg["sanctions_volume"] > 0

st.write(
    "This page highlights wallets with high public risk scores, large volumes, "
    "and sanctions-linked activity based on the public risk model."
)

top_n = st.slider("Number of wallets to show in each list", 5, 30, 10)

# 1) Highest average risk
st.subheader("Top high-risk wallets (by average public score)")
top_high_risk = wallet_agg.sort_values("avg_risk", ascending=False).head(top_n)
st.dataframe(
    top_high_risk[
        [
            "wallet_id",
            "total_volume_usd",
            "n_transactions",
            "avg_risk",
            "max_risk",
            "sanctions_volume",
        ]
    ]
)

# 2) Sanctions-exposed wallets (by sanctions-linked volume)
st.subheader("Sanctions-exposed wallets (by sanctions-linked volume)")
top_sanctions = (
    wallet_agg[wallet_agg["has_sanctions"]]
    .sort_values("sanctions_volume", ascending=False)
    .head(top_n)
)

if not top_sanctions.empty:
    st.dataframe(
        top_sanctions[
            [
                "wallet_id",
                "total_volume_usd",
                "n_transactions",
                "sanctions_volume",
                "avg_risk",
            ]
        ]
    )
else:
    st.info("No sanctions-exposed wallets in the current dataset.")

# 3) Whale wallets (by total volume)
st.subheader("Whale wallets (by total volume)")
top_whales = wallet_agg.sort_values("total_volume_usd", ascending=False).head(top_n)
st.dataframe(
    top_whales[
        [
            "wallet_id",
            "total_volume_usd",
            "n_transactions",
            "avg_risk",
            "sanctions_volume",
        ]
    ]
)