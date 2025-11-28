"""Shared chart creation utilities for the dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px


def create_volume_time_chart(df: pd.DataFrame):
	"""Create volume time series chart.

	Chart functions are intentionally not cached here; caching should be applied
	at the data-loading level so charts render quickly from already-cached data.
	"""
	# Data loader normalizes columns to title case (Date, Hour, Token, Volume)
	if 'Date' not in df.columns or 'Hour' not in df.columns or 'Token' not in df.columns:
		daily = df.groupby(["Date", "Hour", "Token"], as_index=False)["Volume"].sum()
		fig = px.line(daily, x="Hour", y="Volume", color="Token", line_group="Date", markers=False)
		return fig

	# Build hourly datetime (Hour: 1..24 -> offset 0..23)
	df_local = df.copy()
	df_local['__date'] = pd.to_datetime(df_local['Date'], errors='coerce')
	df_local['__hour'] = pd.to_numeric(df_local['Hour'], errors='coerce')
	df_local['datetime'] = df_local['__date'] + pd.to_timedelta(df_local['__hour'] - 1, unit='h')

	# Anchor the rolling window to the latest hour available in the data
	max_dt = df_local['datetime'].max()
	if pd.isna(max_dt):
		# Fallback to original behavior if we can't build datetimes
		daily = df.groupby(["Date", "Hour", "Token"], as_index=False)["Volume"].sum()
		fig = px.line(daily, x="Hour", y="Volume", color="Token", line_group="Date", markers=False)
		return fig

	min_dt = max_dt - pd.Timedelta(hours=23)

	# Restrict to the last 24 hours
	window = df_local[(df_local['datetime'] >= min_dt) & (df_local['datetime'] <= max_dt)].copy()

	# Aggregate by exact hourly timestamp and token
	grouped = (
		window.groupby(['datetime', 'Token'], as_index=False)['Volume']
		.sum()
	)

	# Ensure every token has each hour in the 24h window (fill missing with 0)
	hours = pd.date_range(start=min_dt, end=max_dt, freq='h')
	tokens = grouped['Token'].unique() if not grouped.empty else df_local['Token'].unique()
	idx = pd.MultiIndex.from_product([hours, tokens], names=['datetime', 'Token'])
	grouped = grouped.set_index(['datetime', 'Token']).reindex(idx, fill_value=0).reset_index()

	# Plot with a continuous datetime x-axis
	fig = px.line(grouped, x='datetime', y='Volume', color='Token', line_group='Token', markers=False)
	fig.update_traces(connectgaps=False)
	fig.update_xaxes(title='Hour', tickformat='%H:%M\n%b-%d')

	return fig


def create_token_volume_chart(df: pd.DataFrame):
	"""Create token volume bar chart."""
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


def create_risk_histogram(df: pd.DataFrame, tokens: tuple):
	"""Create risk score histogram - using pre-binned data for performance."""
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


def get_component_scores(df: pd.DataFrame, tokens: tuple) -> pd.DataFrame:
	"""Compute average component scores by token."""
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
