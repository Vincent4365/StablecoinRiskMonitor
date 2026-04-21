import pandas as pd
import plotly.express as px
import streamlit as st

from utils.sidebar import sidebar
from utils.formatting import format_relative_time
from utils.styling import inject_icon_styles
from utils.load_data_new import (
	get_systemic_stablecoin_current,
	get_systemic_stablecoin_summary,
	get_systemic_stablecoin_timeseries,
)

st.set_page_config(
	page_title="Systemic Risk Index - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()


def _fmt_usd(value: object) -> str:
	try:
		if value is None or pd.isna(value):
			return "—"
		v = float(value)
		if abs(v) >= 1_000_000_000:
			return f"${v/1_000_000_000:.2f}B"
		if abs(v) >= 1_000_000:
			return f"${v/1_000_000:.2f}M"
		return f"${v:,.0f}"
	except Exception:
		return "—"


def _fmt_num(value: object, digits: int = 2, suffix: str = "") -> str:
	try:
		if value is None or pd.isna(value):
			return "—"
		return f"{float(value):.{digits}f}{suffix}"
	except Exception:
		return "—"


def _fmt_pct_signed(value: object, digits: int = 3) -> str:
	try:
		if value is None or pd.isna(value):
			return "—"
		return f"{float(value):+.{digits}f}%"
	except Exception:
		return "—"


summary = get_systemic_stablecoin_summary()
current_df, current_asof_ts, _current_last_modified = get_systemic_stablecoin_current()

sidebar_ts = (
	summary.get("asof_ts")
	or current_asof_ts
	or summary.get("last_modified")
	or "Unknown"
)
sidebar(sidebar_ts, show_chain_toggle=False)

st.title("Systemic Risk Index")

with st.container(border=True):
	snapshot_ts = summary.get("asof_ts") or current_asof_ts or "Unknown"
	snapshot_rel = format_relative_time(snapshot_ts, fallback=str(snapshot_ts))

	row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
	row2_c1, row2_c2, row2_c3 = st.columns(3)

	# Aggregate KPI inputs (defensive against empty/missing columns)
	_total_net_issuance = None
	_total_volume_24h = None
	_avg_peg_dev = None
	_ticker_count = None
	if current_df is not None and not current_df.empty:
		if "symbol" in current_df.columns:
			try:
				_ticker_count = int(current_df["symbol"].astype(str).str.upper().nunique())
			except Exception:
				_ticker_count = None
		try:
			if "net_issuance_24h_usd" in current_df.columns:
				_total_net_issuance = pd.to_numeric(current_df["net_issuance_24h_usd"], errors="coerce").sum(min_count=1)
		except Exception:
			_total_net_issuance = None
		try:
			if "volume_24h_usd_avg" in current_df.columns:
				_total_volume_24h = pd.to_numeric(current_df["volume_24h_usd_avg"], errors="coerce").sum(min_count=1)
		except Exception:
			_total_volume_24h = None
		try:
			if "peg_deviation_pct_avg" in current_df.columns:
				_avg_peg_dev = pd.to_numeric(current_df["peg_deviation_pct_avg"], errors="coerce").mean()
		except Exception:
			_avg_peg_dev = None

	with row1_c1:
		st.metric(
			"Total Market Cap",
			_fmt_usd(summary.get("market_cap_total_usd")),
		)
	with row1_c2:
		st.metric("Total Volume (24h)", _fmt_usd(_total_volume_24h))
	with row1_c3:
		st.metric("Total Net Issuance (24h)", _fmt_usd(_total_net_issuance))
	with row1_c4:
		st.metric("Avg Peg Deviation", _fmt_pct_signed(_avg_peg_dev, digits=3))

	with row2_c1:
		st.metric(
			"Average Systemic Risk",
			_fmt_num(summary.get("systemic_risk_avg_0_100"), 2),
		)
	with row2_c2:
		st.metric(
			"Market Cap Weighted Risk",
			_fmt_num(summary.get("systemic_risk_weighted_by_mcap_0_100"), 2),
		)
	with row2_c3:
		st.metric("Tickers", str(_ticker_count) if _ticker_count is not None else "—")


if current_df is None or current_df.empty:
	st.info("No systemic current data available yet.")
	st.stop()

current_df = current_df.copy()
if "symbol" in current_df.columns:
	current_df["symbol"] = current_df["symbol"].astype(str).str.upper()


def _risk_cell_style(value: object) -> str:
	try:
		if value is None or pd.isna(value):
			return ""
		v = float(value)
		v = max(0.0, min(100.0, v))
		# 0 -> green (120deg), 100 -> red (0deg)
		hue = 120.0 * (1.0 - (v / 100.0))
		return f"color: hsl({hue:.0f}, 70%, 35%); font-weight: 600;"
	except Exception:
		return ""


tab_metrics, tab_compare, tab_timeseries = st.tabs(
	["Stablecoin Metrics", "Risk Comparison", "Systemic Timeseries"]
)

with tab_metrics:
	with st.container(border=True):
		view = pd.DataFrame(
			{
				"Ticker": current_df.get("symbol"),
				"Price": pd.to_numeric(current_df.get("price_usd_avg"), errors="coerce"),
				"Market Cap": pd.to_numeric(current_df.get("market_cap_usd_avg"), errors="coerce"),
				"Peg Deviation (%)": pd.to_numeric(current_df.get("peg_deviation_pct_avg"), errors="coerce"),
				"Volume (24h)": pd.to_numeric(current_df.get("volume_24h_usd_avg"), errors="coerce"),
				"Net Issuance (24h)": pd.to_numeric(current_df.get("net_issuance_24h_usd"), errors="coerce"),
				"Risk Score": pd.to_numeric(current_df.get("systemic_risk_score_0_100"), errors="coerce"),
			}
		)

		if "Market Cap" in view.columns:
			view = view.sort_values(["Market Cap", "Ticker"], ascending=[False, True], kind="mergesort")

		styled = (
			view.style
			.format(
				{
					"Price": "${:,.6f}",
					"Market Cap": "${:,.0f}",
					"Peg Deviation (%)": "{:+.3f}%",
					"Volume (24h)": "${:,.0f}",
					"Net Issuance (24h)": "${:,.0f}",
					"Risk Score": "{:,.2f}",
				},
				na_rep="—",
			)
			.applymap(_risk_cell_style, subset=["Risk Score"])
		)
		st.dataframe(styled, hide_index=True, use_container_width=True)

with tab_compare:
	with st.container(border=True):
		plot_df = current_df.copy()
		plot_df["systemic_risk_score_0_100"] = pd.to_numeric(
			plot_df.get("systemic_risk_score_0_100"), errors="coerce"
		)
		plot_df = plot_df.dropna(subset=["systemic_risk_score_0_100"])

		if plot_df.empty:
			st.info("No risk data available for charting.")
		else:
			fig = px.bar(
				plot_df,
				x="symbol",
				y="systemic_risk_score_0_100",
				color="systemic_risk_score_0_100",
				color_continuous_scale="RdYlGn_r",
				title="Systemic Risk Score by Coin",
			)
			fig.update_coloraxes(cmin=0, cmax=100, showscale=False)
			fig.update_yaxes(range=[0, 100])
			fig.update_layout(xaxis_title="", yaxis_title="Risk Score (0-100)")
			st.plotly_chart(fig, use_container_width=True)

with tab_timeseries:
	with st.container(border=True):
		col_coin, col_window = st.columns([1, 1])
		with col_coin:
			selected_ticker = st.selectbox(
				"Coin",
				options=["USDT", "USDC", "DAI", "USDE"],
				index=0,
			)
		with col_window:
			window_hours = st.selectbox("Window", options=[24, 72, 168, 336, 720], index=2)

		timeseries_df, timeseries_asof_ts, timeseries_last_modified = get_systemic_stablecoin_timeseries(
			symbol=selected_ticker,
			hours=int(window_hours),
		)

		if timeseries_df is None or timeseries_df.empty:
			st.info("No timeseries data available for this coin/window.")
		else:
			timeseries_df = timeseries_df.copy()
			fig = px.line(
				timeseries_df,
				x="hour_ts",
				y=["systemic_risk_score_0_100"],
				title=f"{selected_ticker} systemic risk trend",
				labels={"systemic_risk_score_0_100": "Systemic Risk Score"},
			)
			fig.update_yaxes(range=[0, 100])
			fig.update_layout(
				xaxis_title="Hour (UTC)",
				yaxis_title="Risk Score (0-100)",
				legend_title_text="Variable",
			)
			fig.update_traces(name="Systemic Risk Score")
			st.plotly_chart(fig, use_container_width=True)


st.caption(
	"Current systemic-risk view for USDT, USDC, DAI, and USDE. "
	f"Sources: CoinGecko API, CoinPaprika API, DeFiLlama API, DexPaprika API. Snapshot: {snapshot_rel}."
)
