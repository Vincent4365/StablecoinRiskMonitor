import streamlit as st
import pandas as pd
import plotly.express as px


def create_volume_time_chart(df: pd.DataFrame):
	if df.empty:
		return px.line()
	
	if 'datetime' in df.columns:
		df_local = df.copy()
		if not pd.api.types.is_datetime64_any_dtype(df_local['datetime']):
			df_local['datetime'] = pd.to_datetime(df_local['datetime'])
		
		fig = px.line(df_local, x='datetime', y='Volume', color='Token', line_group='Token', markers=False)
		fig.update_traces(connectgaps=False)
		fig.update_xaxes(title='Hour', tickformat='%H:%M\n%b-%d')
		return fig
	
	if 'Date' not in df.columns or 'Hour' not in df.columns or 'Token' not in df.columns:
		return px.line()

	df_local = df.copy()
	df_local['__date'] = pd.to_datetime(df_local['Date'], errors='coerce')
	df_local['__hour'] = pd.to_numeric(df_local['Hour'], errors='coerce')
	df_local['datetime'] = df_local['__date'] + pd.to_timedelta(df_local['__hour'] - 1, unit='h')

	max_dt = df_local['datetime'].max()
	if pd.isna(max_dt):
		return px.line()

	min_dt = max_dt - pd.Timedelta(hours=23)

	window = df_local[(df_local['datetime'] >= min_dt) & (df_local['datetime'] <= max_dt)].copy()

	grouped = (
		window.groupby(['datetime', 'Token'], as_index=False)['Volume']
		.sum()
	)

	hours = pd.date_range(start=min_dt, end=max_dt, freq='h')
	tokens = grouped['Token'].unique() if not grouped.empty else df_local['Token'].unique()
	idx = pd.MultiIndex.from_product([hours, tokens], names=['datetime', 'Token'])
	grouped = grouped.set_index(['datetime', 'Token']).reindex(idx, fill_value=0).reset_index()

	fig = px.line(grouped, x='datetime', y='Volume', color='Token', line_group='Token', markers=False)
	fig.update_traces(connectgaps=False)
	fig.update_xaxes(title='Hour', tickformat='%H:%M\n%b-%d')

	return fig


def create_token_volume_chart(df: pd.DataFrame):
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



def create_risk_histogram_from_api(df: pd.DataFrame):
	if df.empty:
		return px.bar()
	
	df_plot = df.copy()
	df_plot["Risk Score"] = (df_plot["bin_start"] + df_plot["bin_end"]) / 2
	
	fig = px.bar(
		df_plot,
		x="Risk Score",
		y="count",
		color="Token",
		barmode="overlay",
		opacity=0.6,
		labels={"count": "Count", "Risk Score": "Risk score"},
	)
	return fig


