import streamlit as st
import pandas as pd
import plotly.express as px

from utils.sidebar import sidebar
from utils.styling import inject_icon_styles
from utils.formatting import format_volume, format_volume_exact, format_utc_timestamp
from utils.load_data_new import (
	get_dashboard_summary_chain,
	get_rolling_metrics_snapshot_raw,
	get_sanctions_exposure_30d_chain,
)


st.set_page_config(
	page_title="OFAC Sanctions Monitor - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()


def _set_session_value(key: str, value: str) -> None:
	st.session_state[key] = value


def _chain_param_from_ui(chain_label: str) -> str:
	return "Tron" if str(chain_label or "").strip().lower() == "tron" else "Ethereum"


def _best_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
	for c in candidates:
		if c in df.columns:
			return c
	return None


SANCTIONED_ADDRESSES_COUNT_BY_CHAIN = {
	"Ethereum": 77,
	"Tron": 36,
}

header_left, header_right = st.columns([4, 2], vertical_alignment="center")
with header_left:
	st.title("OFAC Sanctions Monitor")
	st.caption("Sanctions list source: OFAC Sanctions List Service (SDN)")

with header_right:
	if "chain" not in st.session_state:
		st.session_state["chain"] = "Ethereum"


with st.container(border=True):
	row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
	with row1_c1:
		_wallets_affected_slot = st.empty()
	with row1_c2:
		_total_sanc_vol_slot = st.empty()
	with row1_c3:
		_max_sanc_vol_slot = st.empty()
	with row1_c4:
		st.caption("Chain")
		c_eth, c_tron = st.columns(2, vertical_alignment="center")
		with c_eth:
			st.button(
				"Ethereum",
				key="ofac_chain_tile_eth",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") != "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Ethereum"),
			)
		with c_tron:
			st.button(
				"Tron",
				key="ofac_chain_tile_tron",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") == "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Tron"),
			)


chain = _chain_param_from_ui(st.session_state.get("chain", "Ethereum"))

sanctioned_addresses_count = SANCTIONED_ADDRESSES_COUNT_BY_CHAIN.get(chain, 0)

dashboard_kpis = get_dashboard_summary_chain(chain=chain, hours=24) or {}
with st.container(border=True):
	k1, k2, k3, k4 = st.columns(4)
	with k1:
		v = dashboard_kpis.get("unique_wallets")
		st.metric("Total wallets tracked", "N/A" if v is None else f"{int(v):,}")
	with k2:
		v = dashboard_kpis.get("total_transactions")
		st.metric("Total transactions (24h)", "N/A" if v is None else f"{int(v):,}")
	with k3:
		v = dashboard_kpis.get("total_volume")
		st.metric("Total volume (24h)", "N/A" if v is None else format_volume(float(v)))
	with k4:
		st.metric("Sanctioned addresses", f"{sanctioned_addresses_count:,}")

rolling_df, asof_ts = get_rolling_metrics_snapshot_raw(
	chain=chain,
	limit=1000,
	order_by="sanctioned_volume_30x24h",
	order="desc",
)

sidebar(last_updated=asof_ts, show_chain_toggle=False)

rolling_df = rolling_df if isinstance(rolling_df, pd.DataFrame) else pd.DataFrame()

wallet_col = _best_col(rolling_df, ["wallet_address", "address", "wallet"]) or "wallet_address"
sanc_vol_col = _best_col(rolling_df, ["sanctioned_volume_30x24h", "sanctioned_volume"]) or "sanctioned_volume_30x24h"
priority_col = _best_col(rolling_df, ["priority_score", "priority"]) or "priority_score"
sanc_score_col = _best_col(rolling_df, ["sanctions_score"]) or "sanctions_score"
ratio_col = _best_col(rolling_df, ["sanctioned_volume_ratio_30d"]) or "sanctioned_volume_ratio_30d"

if rolling_df.empty:
	affected_mask = pd.Series([], dtype=bool)
	_wallets_affected_slot.metric("Wallets affected", "0")
	_total_sanc_vol_slot.metric("Sanctioned volume (30d)", format_volume(0.0))
	_max_sanc_vol_slot.metric("Max wallet sanctioned volume", format_volume(0.0))
else:
	sanc_vol = pd.to_numeric(rolling_df.get(sanc_vol_col), errors="coerce").fillna(0.0)
	affected_mask = sanc_vol > 0

	wallets_affected = int(affected_mask.sum())
	total_sanc_vol = float(sanc_vol.loc[affected_mask].sum()) if wallets_affected else 0.0
	max_sanc_vol = float(sanc_vol.max()) if len(sanc_vol) else 0.0

	_wallets_affected_slot.metric("Wallets affected", f"{wallets_affected:,}")
	_total_sanc_vol_slot.metric("Sanctioned volume (30d)", format_volume(total_sanc_vol))
	_max_sanc_vol_slot.metric("Max wallet sanctioned volume", format_volume(max_sanc_vol))

tab_overview, tab_top_wallets, tab_exposure = st.tabs(
	[
		":material/overview: Overview",
		":material/table_view: Top wallets",
		":material/hub: Exposure (by token)",
	]
)

with tab_overview:
	with st.container(border=True):
		st.subheader("Overview")
		if rolling_df.empty:
			st.info(f"No sanctioned transactions in the current dataset as of {format_utc_timestamp(asof_ts)}.")
		else:
			st.write(
				"This page surfaces sanctions-related activity signals derived from the project-maintained OFAC list. "
				"Metrics are computed from stablecoin transfer flows and aggregated into hourly + rolling windows."
			)

			view = rolling_df.loc[affected_mask].copy()
			if view.empty:
				st.info(f"No wallets with non-zero sanctioned volume as of {format_utc_timestamp(asof_ts)}.")
			else:
				vals = pd.to_numeric(view[sanc_vol_col], errors="coerce").dropna()
				if vals.empty:
					st.info("Sanctioned volume data not available.")
				else:
					fig = px.histogram(
						vals,
						nbins=40,
						title="Distribution of wallet sanctioned volume (30d)",
					)
					fig.update_layout(xaxis_title="Sanctioned volume (USD, 30d)", yaxis_title="Wallets")
					st.plotly_chart(fig, use_container_width=True)

with tab_top_wallets:
	with st.container(border=True):
		st.subheader("Top 10 sanctioned wallets by volume")
		if rolling_df.empty:
			st.info(f"No sanctioned transactions in the current dataset as of {format_utc_timestamp(asof_ts)}.")
		else:

			view = rolling_df.copy()
			view[sanc_vol_col] = pd.to_numeric(view.get(sanc_vol_col), errors="coerce").fillna(0.0)
			view = view.loc[view[sanc_vol_col] > 0].copy()
			if view.empty:
				st.info(f"No wallets with non-zero sanctioned volume as of {format_utc_timestamp(asof_ts)}.")
			else:
				view = view.sort_values(sanc_vol_col, ascending=False, kind="mergesort").head(10).copy()

				# Chart
				fig = px.bar(
					view,
					x=wallet_col,
					y=sanc_vol_col,
					title="Top 10 wallets by sanctioned volume (30d)",
				)
				fig.update_layout(xaxis_title="Wallet", yaxis_title="Sanctioned volume (USD, 30d)")
				st.plotly_chart(fig, use_container_width=True)

				# Table
				out = pd.DataFrame(
					{
						"Wallet": view[wallet_col].astype(str),
						"Sanctioned Volume (30d)": pd.to_numeric(view[sanc_vol_col], errors="coerce"),
						"Sanctioned Ratio (30d)": pd.to_numeric(view.get(ratio_col), errors="coerce") if ratio_col in view.columns else None,
						"Sanctions Score": pd.to_numeric(view.get(sanc_score_col), errors="coerce") if sanc_score_col in view.columns else None,
						"Priority Score": pd.to_numeric(view.get(priority_col), errors="coerce") if priority_col in view.columns else None,
					}
				)

				st.dataframe(
					out,
					hide_index=True,
					use_container_width=True,
					column_config={
						"Wallet": st.column_config.TextColumn("Wallet"),
						"Sanctioned Volume (30d)": st.column_config.NumberColumn(
							"Sanctioned Volume (30d)",
							format="$%.2f",
						),
						"Sanctioned Ratio (30d)": st.column_config.NumberColumn(
							"Sanctioned Ratio (30d)",
							format="%.4f",
						),
						"Sanctions Score": st.column_config.NumberColumn("Sanctions Score", format="%.2f"),
						"Priority Score": st.column_config.NumberColumn("Priority Score", format="%.2f"),
					},
				)

				st.caption("Note: 'Sanctioned volume' is volume in transactions involving an OFAC-listed address (directly).")

with tab_exposure:
	with st.container(border=True):
		st.subheader("Token-level sanctions exposure (last 30 days)")
		exp_df, last_modified = get_sanctions_exposure_30d_chain(chain=chain)

		if exp_df is None or exp_df.empty:
			st.info("No exposure export available.")
		else:
			if "token_symbol" in exp_df.columns and "direct_sanctioned_volume" in exp_df.columns:
				plot_df = exp_df.copy()
				plot_df["direct_sanctioned_volume"] = pd.to_numeric(plot_df["direct_sanctioned_volume"], errors="coerce").fillna(0.0)
				fig = px.bar(
					plot_df,
					x="token_symbol",
					y="direct_sanctioned_volume",
					title="Direct sanctioned volume by token (30d)",
				)
				fig.update_layout(xaxis_title="Token", yaxis_title="Direct sanctioned volume (USD, 30d)")
				st.plotly_chart(fig, use_container_width=True)

			# Table
			pretty = exp_df.copy()
			for c in (
				"direct_sanctioned_volume",
				"one_hop_volume_with_sanctions",
				"two_hop_volume_capped",
			):
				if c in pretty.columns:
					pretty[c] = pd.to_numeric(pretty[c], errors="coerce")
					pretty[c] = pretty[c].map(lambda v: format_volume_exact(float(v)) if pd.notna(v) else "")

			st.dataframe(pretty, hide_index=True, use_container_width=True)
			if last_modified:
				st.caption(f"Export last modified: {last_modified}")
