"""Shared formatting and aggregation utilities for the dashboard."""
import streamlit as st
import pandas as pd

def format_volume(value):
	"""Format large numbers more compactly (e.g., $51.2B instead of $51,199,081)."""
	if value >= 1_000_000_000:
		return f"${value/1_000_000_000:.2f}B"
	elif value >= 1_000_000:
		return f"${value/1_000_000:.2f}M"
	elif value >= 1_000:
		return f"${value/1_000:.2f}K"
	else:
		return f"${value:.2f}"

@st.cache_data
def get_wallet_aggregation(df: pd.DataFrame) -> pd.DataFrame:
	"""Cache the expensive wallet-level aggregation."""
	df_copy = df.copy()
	df_copy["sanctioned_volume"] = df_copy["Volume"] * df_copy["Sanctioned"]
	
	wallet_agg = (
		df_copy.groupby("Wallet", as_index=False)
		.agg(
			Total_Volume=("Volume", "sum"),
			N_Transactions=("Volume", "count"),
			Avg_Risk=("Risk Score", "mean"),
			Max_Risk=("Risk Score", "max"),
			Sanctioned_Volume=("sanctioned_volume", "sum"),
		)
	)
	
	wallet_agg = wallet_agg.rename(columns={
		"Total_Volume": "Total Volume",
		"N_Transactions": "Transactions",
		"Avg_Risk": "Average Risk",
		"Max_Risk": "Max Risk",
		"Sanctioned_Volume": "Sanctioned Volume"
	})
	
	return wallet_agg.sort_values(["Average Risk"], ascending=[False])
