import streamlit as st
import pandas as pd
import plotly.express as px


def get_token_color_map(df: pd.DataFrame, token_order: list | None = None) -> dict:
	if df is None or df.empty or "Token" not in df.columns:
		return {}
	palette = px.colors.qualitative.Plotly
	tokens = token_order if token_order is not None else list(pd.unique(df["Token"]))
	color_map = {token: palette[i % len(palette)] for i, token in enumerate(tokens)}

	# Manual tweak: swap DAI and USDT colors for consistency with prior visuals.
	def _find_key(name: str) -> str | None:
		needle = name.casefold()
		for k in color_map.keys():
			if str(k).casefold() == needle:
				return k
		return None

	dai_key = _find_key("DAI")
	usdt_key = _find_key("USDT")
	if dai_key is not None and usdt_key is not None:
		color_map[dai_key], color_map[usdt_key] = color_map[usdt_key], color_map[dai_key]

	return color_map


def create_volume_time_chart(df: pd.DataFrame, color_map: dict | None = None):
	if df.empty:
		return px.line()

	color_map = color_map or get_token_color_map(df)
	
	if 'datetime' in df.columns:
		df_local = df.copy()
		if not pd.api.types.is_datetime64_any_dtype(df_local['datetime']):
			df_local['datetime'] = pd.to_datetime(df_local['datetime'])
		
		show_markers = df_local['datetime'].nunique(dropna=True) <= 1
		fig = px.line(
			df_local,
			x='datetime',
			y='Volume',
			color='Token',
			line_group='Token',
			markers=show_markers,
			color_discrete_map=color_map,
		)
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

	fig = px.line(
		grouped,
		x='datetime',
		y='Volume',
		color='Token',
		line_group='Token',
		markers=False,
		color_discrete_map=color_map,
	)
	fig.update_traces(connectgaps=False)
	fig.update_xaxes(title='Hour', tickformat='%H:%M\n%b-%d')

	return fig


def create_token_volume_chart(df: pd.DataFrame):
	vol_token = df.groupby("Token", as_index=False)["Volume"].sum()
	# Sort ascending so the largest ends up at the top for a horizontal bar chart.
	vol_token = vol_token.sort_values("Volume", ascending=True)
	token_order = vol_token["Token"].tolist()
	color_map = get_token_color_map(df, token_order=token_order)
	fig = px.bar(
		vol_token,
		x="Volume",
		y="Token",
		color="Token",
		orientation="h",
		text="Volume",
		color_discrete_map=color_map,
		category_orders={"Token": token_order},
	)
	fig.update_traces(texttemplate="%{text:,.0f}")
	fig.update_layout(showlegend=False)
	# Lock ordering deterministically.
	fig.update_yaxes(categoryorder="array", categoryarray=token_order)
	return fig



def create_risk_histogram_from_api(df: pd.DataFrame):
	if df.empty:
		return px.bar()
	
	df_plot = df.copy()
	# Some sources may return these as Categoricals/objects; ensure numeric before arithmetic.
	df_plot["bin_start"] = pd.to_numeric(df_plot.get("bin_start"), errors="coerce")
	df_plot["bin_end"] = pd.to_numeric(df_plot.get("bin_end"), errors="coerce")
	df_plot = df_plot[df_plot["bin_start"].notna() & df_plot["bin_end"].notna()]
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


