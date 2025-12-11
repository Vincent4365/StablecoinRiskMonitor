import streamlit as st
import pandas as pd
import plotly.express as px
from utils.load_data import get_top_wallets, get_dashboard_summary, get_last_updated
from utils.sidebar import sidebar
from utils.formatting import format_volume
from utils.styling import inject_icon_styles

inject_icon_styles()

last_updated = get_last_updated()
sidebar(last_updated)

st.title("Risk Alerts")
st.caption(
	"This page highlights wallets with high risk scores, large volumes, and sanctions-linked activity."
)

with st.container(border=True):
	st.header("High-Risk Wallets")

	top_n = st.slider("Number of wallets:", 5, 100, 25)

	st.subheader("Top high-risk wallets (by average risk score)")
	top_high_risk = get_top_wallets(top_n=top_n, sort_by='risk')
	
	if not top_high_risk.empty:
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
	else:
		st.info("No high-risk wallet data available")

	st.subheader("Whale wallets (by total volume)")
	top_whales = get_top_wallets(top_n=top_n, sort_by='volume')
	
	if not top_whales.empty:
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
	else:
		st.info("No whale wallet data available")

with st.container(border=True):
	st.header("Sanctions-Linked Activity")

	summary = get_dashboard_summary()
	
	if summary:
		total_vol = summary.get("total_volume", 0)
		sanctioned_vol = summary.get("sanctioned_volume", 0)
		sanctioned_pct = (sanctioned_vol / total_vol * 100) if total_vol > 0 else 0
		flagged_wallets = summary.get("sanctioned_wallets", 0)
		sanctioned_tx_count = summary.get("sanctioned_transactions", 0)

		col1, col2, col3, col4 = st.columns(4)
		with col1:
			st.metric("Sanctioned Volume", format_volume(sanctioned_vol))
		with col2:
			st.metric("Share of Total", f"{sanctioned_pct:.2f}%")
		with col3:
			st.metric("Flagged Wallets", flagged_wallets)
		with col4:
			st.metric("Sanctioned Txs", sanctioned_tx_count)
	else:
		st.info("No summary data available")

	st.divider()

	st.subheader("Sanctions-exposed wallets")
	top_sanctions = get_top_wallets(top_n=top_n, sort_by='sanctions')
	
	if not top_sanctions.empty:
		top_sanctions_filtered = top_sanctions[top_sanctions["Sanctioned Volume"] > 0]
		
		if not top_sanctions_filtered.empty:
			st.dataframe(
				top_sanctions_filtered[
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
	else:
		st.info("No sanctions-exposed wallets in the current dataset.")