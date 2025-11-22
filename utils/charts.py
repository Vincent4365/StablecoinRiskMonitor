"""Shared chart creation utilities for the dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px


@st.cache_data
def create_volume_time_chart(df: pd.DataFrame):
	"""Create volume time series chart with caching."""
	daily = df.groupby(["Date", "Hour", "Token"], as_index=False)["Volume"].sum()
	fig = px.line(
		daily,
		x="Hour",
		y="Volume",
		color="Token",
		line_group="Date",
		markers=False,
	)
	return fig


@st.cache_data
def create_token_volume_chart(df: pd.DataFrame):
	"""Create token volume bar chart with caching."""
	vol_token = df.groupby("Token", as_index=False)["Volume"].sum()
	vol_token = vol_token.sort_values("Volume", ascending=True)
	fig = px.bar(
		vol_token,
		x="Volume",
		y="Token",
		orientation="h",
		text="Volume",
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	return fig


@st.cache_data
def create_risk_histogram(df: pd.DataFrame, tokens: tuple):
	"""Create risk score histogram with caching - using pre-binned data for performance."""
	filtered_df = df[df["Token"].isin(tokens)]
	
	# Pre-bin the data to reduce plotly processing time
	bins = pd.cut(filtered_df["Risk Score"], bins=30, include_lowest=True)
	hist_data = (
		filtered_df.groupby([bins, "Token"], observed=True)
		.size()
		.reset_index(name="count")
	)
	hist_data["Risk Score"] = hist_data["Risk Score"].apply(lambda x: x.mid)
	
	fig = px.bar(
		hist_data,
		x="Risk Score",
		y="count",
		color="Token",
		barmode="overlay",
		opacity=0.6,
		labels={"count": "Count", "Risk Score": "Public risk score"},
	)
	return fig


@st.cache_data
def get_component_scores(df: pd.DataFrame, tokens: tuple) -> pd.DataFrame:
	"""Compute average component scores by token with caching."""
	filtered_df = df[df["Token"].isin(tokens)]
	return filtered_df.groupby("Token", as_index=False)[
		[
			"Volume Score",
			"Token Score",
			"Concentration Score",
			"Velocity Score",
			"Sanctions Score",
			"Burst Score",
			"Time Score",
			"Risk Score",
		]
	].mean()
