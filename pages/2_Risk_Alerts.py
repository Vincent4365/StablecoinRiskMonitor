import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import load_demo_data, load_real_data
from utils.sidebar import sidebar
from utils.formatting import format_volume, get_wallet_aggregation
from utils.styling import inject_icon_styles

inject_icon_styles()

data_source = sidebar()

st.title("Risk Alerts")
st.caption(
	"This page highlights wallets with high risk scores, large volumes, and sanctions-linked activity."
)

if data_source.startswith("Demo"):
	df = load_demo_data()
else:
	df = load_real_data()

if df.empty:
	st.info("No data available.")
	st.stop()

wallet_agg = get_wallet_aggregation(df)

with st.container(border=True):
	st.header("High-Risk Wallets")

	top_n = st.slider("Number of wallets:", 5, 100, 25)

	st.subheader("Top high-risk wallets (by average risk score)")
	top_high_risk = wallet_agg.head(top_n)
	st.dataframe(
		top_high_risk[
			[
				"Wallet",
				"Total Volume",
				"Transactions",
				"Average Risk",
				"Max Risk",
				"Sanctioned Volume",
			]
		],
		use_container_width=True,
		hide_index=True
	)

	st.subheader("Whale wallets (by total volume)")
	top_whales = wallet_agg.sort_values("Total Volume", ascending=False).head(top_n)
	st.dataframe(
		top_whales[
			[
				"Wallet",
				"Total Volume",
				"Transactions",
				"Average Risk",
				"Sanctioned Volume",
			]
		],
		use_container_width=True,
		hide_index=True
	)

with st.container(border=True):
	st.header("Sanctions-Linked Activity")

	total_vol = df["Volume"].sum()
	sanctioned_vol = df.loc[df["Sanctioned"] == 1, "Volume"].sum()
	sanctioned_pct = (sanctioned_vol / total_vol * 100) if total_vol > 0 else 0
	flagged_wallets = df.loc[df["Sanctioned"] == 1, "Wallet"].nunique()
	sanctioned_tx_count = (df["Sanctioned"] == 1).sum()

	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Sanctioned Volume", format_volume(sanctioned_vol))
	with col2:
		st.metric("Share of Total", f"{sanctioned_pct:.2f}%")
	with col3:
		st.metric("Flagged Wallets", flagged_wallets)
	with col4:
		st.metric("Sanctioned Txs", sanctioned_tx_count)

	st.divider()

	st.subheader("Sanctions-exposed wallets")
	top_sanctions = (
		wallet_agg[wallet_agg["Sanctioned Volume"] > 0]
		.sort_values("Sanctioned Volume", ascending=False)
		.head(top_n)
	)

	if not top_sanctions.empty:
		st.dataframe(
			top_sanctions[
				[
					"Wallet",
					"Total Volume",
					"Transactions",
					"Sanctioned Volume",
					"Average Risk",
				]
			],
			use_container_width=True,
			hide_index=True
		)
	else:
		st.info("No sanctions-exposed wallets in the current dataset.")