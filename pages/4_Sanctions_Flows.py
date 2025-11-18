import streamlit as st
import plotly.express as px
import pandas as pd

from utils.load_data import load_demo_data

st.title("Sanctions-linked Flows")

df = load_demo_data()

if "sanctions_flag" not in df.columns:
    st.warning("Current dataset has no 'sanctions_flag' column.")
    st.stop()

# Ensure proper type
df["sanctions_flag"] = df["sanctions_flag"].astype(int)

# Label for plotting
df["sanctions_status"] = df["sanctions_flag"].map(
    {0: "Clean", 1: "Sanction-linked"}
)

st.subheader("Filters")

tokens = st.multiselect(
    "Filter by token",
    sorted(df["token"].unique()),
    default=sorted(df["token"].unique()),
)

df = df[df["token"].isin(tokens)]

date_min = df["date"].min()
date_max = df["date"].max()

date_range = st.date_input(
    "Date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))]

st.subheader("Key figures")

total_vol = df["tx_volume_usd"].sum()
sanctioned_vol = df.loc[df["sanctions_flag"] == 1, "tx_volume_usd"].sum()
sanctioned_pct = (sanctioned_vol / total_vol * 100) if total_vol > 0 else 0
flagged_wallets = df.loc[df["sanctions_flag"] == 1, "wallet_id"].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total volume (USD)", f"${total_vol:,.0f}")
with col2:
    st.metric("Sanctions-linked volume (USD)", f"${sanctioned_vol:,.0f}")
with col3:
    st.metric("Sanctions-linked share", f"{sanctioned_pct:.2f}%")
with col4:
    st.metric("Flagged wallets", flagged_wallets)

st.markdown("---")

st.subheader("Volume over time: clean vs sanctions-linked")

daily = (
    df.groupby(["date", "sanctions_status"], as_index=False)["tx_volume_usd"]
    .sum()
    .rename(columns={"tx_volume_usd": "daily_volume_usd"})
)

if not daily.empty:
    fig_ts = px.area(
        daily.sort_values("date"),
        x="date",
        y="daily_volume_usd",
        color="sanctions_status",
        labels={
            "date": "Date",
            "daily_volume_usd": "Volume (USD)",
            "sanctions_status": "Status",
        },
    )
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.info("No data for selected filters.")

st.subheader("Sanctions-linked volume by token")

sanctioned_only = df[df["sanctions_flag"] == 1]

if not sanctioned_only.empty:
    vol_by_token = (
        sanctioned_only.groupby("token", as_index=False)["tx_volume_usd"].sum()
        .rename(columns={"tx_volume_usd": "sanctioned_volume_usd"})
    )

    fig_token = px.bar(
        vol_by_token,
        x="token",
        y="sanctioned_volume_usd",
        text="sanctioned_volume_usd",
        labels={
            "token": "Token",
            "sanctioned_volume_usd": "Sanctions-linked volume (USD)",
        },
    )
    fig_token.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        width=0.4,
    )
    fig_token.update_layout(bargap=0.5)
    st.plotly_chart(fig_token, use_container_width=True)
else:
    st.info("No sanctions-linked volume for the selected filters.")

st.subheader("Flagged wallets")

min_vol = st.slider(
    "Minimum cumulative volume per wallet (USD)",
    min_value=0,
    max_value=int(df["tx_volume_usd"].max() if not df.empty else 0),
    value=0,
    step=10000,
)

if not sanctioned_only.empty:
    wallet_agg = (
        sanctioned_only
        .groupby("wallet_id", as_index=False)
        .agg(
            total_volume_usd=("tx_volume_usd", "sum"),
            n_transactions=("tx_volume_usd", "count"),
        )
    )

    wallet_agg = wallet_agg[wallet_agg["total_volume_usd"] >= min_vol]
    wallet_agg = wallet_agg.sort_values("total_volume_usd", ascending=False)

    st.dataframe(wallet_agg)
else:
    st.info("No flagged wallets for the selected filters.")