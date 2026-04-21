import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from urllib.parse import quote_plus

from utils.load_data_new import (
	get_dashboard_summary_chain,
	get_top_wallets_chain,
	get_timeseries_data_chain,
	get_token_volume_chain,
	get_rolling_metrics_snapshot_raw,
	get_systemic_stablecoin_current,
	get_systemic_stablecoin_summary,
	get_last_updated,
)
from utils.sidebar import sidebar
from utils.formatting import format_volume, format_volume_exact, format_utc_timestamp
from utils.charts import create_volume_time_chart, create_token_volume_chart, get_token_color_map
from utils.styling import inject_icon_styles

st.set_page_config(
	page_title="Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()


def _force_same_tab_wallet_links() -> None:
	"""Force Wallet Analysis links to open in the same tab.

	Streamlit renders markdown/link columns with `target=_blank` by default.
	We rewrite those anchors so clicking a wallet navigates within the same tab.
	"""
	components.html(
		"""
<script>
(function () {
	const selector = 'a[href*="Wallet_Analysis?wallet="]';
	function fixTargets() {
		try {
			const doc = (window.parent && window.parent.document) ? window.parent.document : document;
			const links = doc.querySelectorAll(selector);
			links.forEach((a) => a.setAttribute('target', '_self'));
		} catch (e) {
			// no-op
		}
	}
	fixTargets();
	let runs = 0;
	const id = setInterval(() => {
		fixTargets();
		runs += 1;
		if (runs >= 12) clearInterval(id);
	}, 250);
})();
</script>
""",
		height=0,
	)


def _risk_cell_style(value: object) -> str:
	"""Match the Systemic Risk Index table styling for risk scores."""
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


TOP_N_OPTIONS = [10, 25, 50, 100, 250, 500, 1000]
TOP_N_VALUE_KEY = "top_n_priority_wallets_value"
TOP_N_MAIN_WIDGET_KEY = "top_n_priority_wallets_main"
TOP_N_VOLUME_WIDGET_KEY = "top_n_priority_wallets_volume"


def _set_top_n_from(widget_key: str) -> None:
	st.session_state[TOP_N_VALUE_KEY] = int(st.session_state.get(widget_key, 100) or 100)


def _set_session_value(key: str, value: str) -> None:
	st.session_state[key] = value


if TOP_N_VALUE_KEY not in st.session_state:
	# Migrate from older key if present.
	st.session_state[TOP_N_VALUE_KEY] = int(st.session_state.get("top_n_priority_wallets", 100) or 100)

# If the canonical value changed, clear stale widget state so both dropdowns
# re-initialize cleanly to the same value.
canonical_top_n = int(st.session_state.get(TOP_N_VALUE_KEY, 100) or 100)
if st.session_state.get(TOP_N_MAIN_WIDGET_KEY) not in (None, canonical_top_n):
	del st.session_state[TOP_N_MAIN_WIDGET_KEY]
if st.session_state.get(TOP_N_VOLUME_WIDGET_KEY) not in (None, canonical_top_n):
	del st.session_state[TOP_N_VOLUME_WIDGET_KEY]
# Remove the legacy widget key if it exists.
if "top_n_priority_wallets" in st.session_state:
	del st.session_state["top_n_priority_wallets"]


def _metric_na(v, fmt=None) -> str:
	if v is None:
		return "N/A"
	if fmt is None:
		return str(v)
	return fmt(v)


if "chain" not in st.session_state:
	st.session_state["chain"] = "Ethereum"

chain = st.session_state.get("chain", "Ethereum")
last_updated = get_last_updated(chain=chain)

sidebar(last_updated, show_chain_toggle=False)

header_left, header_right = st.columns([4, 2], vertical_alignment="center")
with header_left:
	st.title("Stablecoin Risk Monitor")

with header_right:
	# Chain selector lives inside the KPI container below.
	pass

# Snapshot KPIs are 24h-only for now.
selected_hours = 24

chain = st.session_state.get("chain", "Ethereum")

summary = get_dashboard_summary_chain(chain=chain, hours=selected_hours)

if not summary:
	st.info("No data available.")
	st.stop()

date_range = summary.get("date_range", {})
date_start = date_range.get("start", "N/A")

# Preload token volume so both charts share the exact same token colors.
token_df = get_token_volume_chain(chain=chain, hours=selected_hours)
token_color_map = None
if token_df is not None and not token_df.empty and "Token" in token_df.columns and "Volume" in token_df.columns:
	# Match the bar chart's ordering (ascending volume) so colors align exactly.
	vol_token = token_df.groupby("Token", as_index=False)["Volume"].sum().sort_values("Volume", ascending=True)
	token_color_map = get_token_color_map(token_df, token_order=vol_token["Token"].tolist())
date_end = date_range.get("end", "N/A")

with st.container(border=True):
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		unique_wallets = summary.get("unique_wallets")
		st.metric("Unique Wallets", "N/A" if unique_wallets is None else f"{unique_wallets:,}")
	with col2:
		st.metric("Total Volume", _metric_na(summary.get("total_volume"), format_volume))
	with col3:
		total_tx = summary.get("total_transactions")
		st.metric("Total Transactions", "N/A" if total_tx is None else f"{total_tx:,}")
	with col4:
		st.caption("Chain")
		eth_col, tron_col = st.columns([1.2, 1.0], vertical_alignment="center")
		with eth_col:
			st.button(
				"Ethereum",
				key="chain_btn_eth_1b",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") != "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Ethereum"),
			)
		with tron_col:
			st.button(
				"Tron",
				key="chain_btn_tron_1b",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") == "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Tron"),
			)


tab1, tab2, tab3, tab4 = st.tabs([
	":material/gpp_maybe: Top Priority Wallets",
	":material/paid: Top Volume Wallets",
	":material/show_chart: Volume Over Time",
	":material/bar_chart: Volume by Token",
])

with tab1:
	with st.container(border=True):
		hdr_left, hdr_right = st.columns([2.2, 1.8], vertical_alignment="center")
		with hdr_left:
			st.subheader("Top Priority Wallets")
		with hdr_right:
			show_label_col, show_select_col, nav_col = st.columns([0.3, 0.7, 1.4], vertical_alignment="center")
			with show_label_col:
				st.caption("Show")
			with show_select_col:
				current_top_n = int(st.session_state.get(TOP_N_VALUE_KEY, 100) or 100)
				st.selectbox(
					"Wallets to show",
					options=TOP_N_OPTIONS,
					index=TOP_N_OPTIONS.index(current_top_n) if current_top_n in TOP_N_OPTIONS else 0,
					key=TOP_N_MAIN_WIDGET_KEY,
					on_change=_set_top_n_from,
					args=(TOP_N_MAIN_WIDGET_KEY,),
					label_visibility="collapsed",
				)
			with nav_col:
				if st.button("Go to Advanced Analysis", use_container_width=True):
					if hasattr(st, "switch_page"):
						st.switch_page("pages/7_Advanced_Analysis.py")
					else:
						st.info("Open 'Advanced Analysis' from the page list.")

		# Use the canonical value for downstream calls.
		top_n = int(st.session_state.get(TOP_N_VALUE_KEY, 100) or 100)
		top_wallets = get_top_wallets_chain(chain=chain, top_n=top_n, sort_by='risk', hours=selected_hours)

		if not top_wallets.empty:
			display_df = top_wallets[[
				"Rank",
				"Wallet",
				"Priority Score",
				"24h Volume",
				"24h Txns",
				"Counterparties",
			]].copy()

			# Make the wallet address itself clickable (no row-selection UI).
			chain_param = "tron" if st.session_state.get("chain", "Ethereum") == "Tron" else "eth"
			display_df["Wallet"] = display_df["Wallet"].astype(str).apply(
				lambda w: f"Wallet_Analysis?wallet={quote_plus(str(w))}&chain={chain_param}"
			)
			display_df = display_df.rename(
				columns={
					"24h Txns": "24h Transactions",
					"Counterparties": "24h Counterparties",
				}
			)
			display_df = display_df.set_index("Rank")
			display_df.index.name = "#"

			st.dataframe(
				display_df,
				hide_index=False,
				use_container_width=True,
				column_config={
					"Wallet": st.column_config.LinkColumn(
						"Wallet",
						display_text=r"wallet=([^&]+)",
						width="medium",
					),
					"Priority Score": st.column_config.ProgressColumn(
						"Priority Score",
						min_value=0,
						max_value=100,
						format="%.1f",
					),
					"24h Volume": st.column_config.NumberColumn("24h Volume", format="$%.2f"),
					"24h Transactions": st.column_config.NumberColumn("24h Transactions", format="%d"),
					"24h Counterparties": st.column_config.NumberColumn("24h Counterparties", format="%d"),
				},
			)
			_force_same_tab_wallet_links()
		else:
			st.info("No wallet data available")


	with st.container(border=True):
		hdr_left, hdr_right = st.columns([3, 1], vertical_alignment="center")
		with hdr_left:
			st.subheader("OFAC Sanctions Overview")
		with hdr_right:
			if st.button("Go to Sanctions Monitor", use_container_width=True):
				if hasattr(st, "switch_page"):
					st.switch_page("pages/3_OFAC_Sanctions_Monitor.py")
				else:
					st.info("Open 'OFAC Sanctions Monitor' from the page list.")

		rolling_df, _rolling_asof_ts = get_rolling_metrics_snapshot_raw(
			chain=chain,
			limit=250,
			order_by="sanctioned_volume_30x24h",
			order="desc",
		)
		asof_utc = format_utc_timestamp(_rolling_asof_ts)
		rolling_df = rolling_df if isinstance(rolling_df, pd.DataFrame) else pd.DataFrame()
		sanc_col = "sanctioned_volume_30x24h" if "sanctioned_volume_30x24h" in rolling_df.columns else "sanctioned_volume"
		sanc_vol = (
			pd.to_numeric(rolling_df.get(sanc_col), errors="coerce").fillna(0.0)
			if not rolling_df.empty and sanc_col in rolling_df.columns
			else pd.Series([0.0])
		)
		has_sanctioned_activity = bool((sanc_vol > 0).any())
		if has_sanctioned_activity:
			st.markdown(
				f":material/warning: Sanctioned transactions detected in the current dataset (as of {asof_utc})"
			)
		else:
			st.markdown(
				f":material/check_circle: No sanctioned transactions detected in the current dataset (as of {asof_utc})"
			)

	with st.container(border=True):
		hdr_left, hdr_right = st.columns([3, 1], vertical_alignment="center")
		with hdr_left:
			st.subheader("Systemic Risk Overview")
		with hdr_right:
			if st.button("Go to Systemic Risk Index", use_container_width=True):
				if hasattr(st, "switch_page"):
					st.switch_page("pages/2_Systemic_Risk_Index.py")
				else:
					st.info("Open 'Systemic Risk Index' from the page list.")

		sys_summary = get_systemic_stablecoin_summary() or {}
		sys_df, _sys_asof_ts, _sys_last_modified = get_systemic_stablecoin_current()
		sys_df = sys_df if isinstance(sys_df, pd.DataFrame) else pd.DataFrame()

		wanted = ["USDT", "USDC", "DAI", "USDE"]
		if not sys_df.empty and "symbol" in sys_df.columns:
			sys_df = sys_df.copy()
			sys_df["symbol"] = sys_df["symbol"].astype(str).str.upper()
			view = sys_df[sys_df["symbol"].isin(wanted)].copy()
		else:
			view = pd.DataFrame(columns=["symbol", "peg_deviation_pct_avg", "systemic_risk_score_0_100"])

		if view.empty:
			st.info("No systemic snapshot available.")
		else:
			view = view[[
				"symbol",
				"peg_deviation_pct_avg",
				"systemic_risk_score_0_100",
			]].copy()
			view = view.drop_duplicates(subset=["symbol"], keep="first")
			view["_order"] = pd.Categorical(view["symbol"], categories=wanted, ordered=True)
			view = view.sort_values("_order").drop(columns=["_order"])
			view = view.rename(
				columns={
					"symbol": "Ticker",
					"peg_deviation_pct_avg": "Peg Deviation (%)",
					"systemic_risk_score_0_100": "Risk Score",
				}
			)
			if "Risk Score" in view.columns:
				view["Risk Score"] = pd.to_numeric(view["Risk Score"], errors="coerce")
			st.dataframe(
				view.style.applymap(_risk_cell_style, subset=["Risk Score"]),
				hide_index=True,
				use_container_width=True,
				column_config={
					"Ticker": st.column_config.TextColumn("Ticker", width="small"),
					"Peg Deviation (%)": st.column_config.NumberColumn("Peg Deviation (%)", format="%+.3f%%"),
					"Risk Score": st.column_config.NumberColumn("Risk Score", format="%.2f"),
				},
			)


with tab2:
	with st.container(border=True):
		col_title, col_ctrl = st.columns([3, 1], vertical_alignment="center")
		with col_title:
			st.subheader("Top Volume Wallets")
		with col_ctrl:
			label_col, select_col = st.columns([1, 3], vertical_alignment="center")
			with label_col:
				st.caption("Show")
			with select_col:
				current_top_n = int(st.session_state.get(TOP_N_VALUE_KEY, 10) or 10)
				top_n = st.selectbox(
					"Wallets to show",
					options=TOP_N_OPTIONS,
					index=TOP_N_OPTIONS.index(current_top_n) if current_top_n in TOP_N_OPTIONS else 0,
					key=TOP_N_VOLUME_WIDGET_KEY,
					on_change=_set_top_n_from,
					args=(TOP_N_VOLUME_WIDGET_KEY,),
					label_visibility="collapsed",
				)
				# Use the canonical value for downstream calls.
				top_n = int(st.session_state.get(TOP_N_VALUE_KEY, top_n) or top_n)

		top_wallets = get_top_wallets_chain(chain=chain, top_n=top_n, sort_by='volume', hours=selected_hours)

		if not top_wallets.empty:
			display_df = top_wallets[[
				"Rank",
				"Wallet",
				"Priority Score",
				"24h Volume",
				"24h Txns",
				"Counterparties",
			]].copy()

			# Make the wallet address itself clickable (no row-selection UI).
			chain_param = "tron" if st.session_state.get("chain", "Ethereum") == "Tron" else "eth"
			display_df["Wallet"] = display_df["Wallet"].astype(str).apply(
				lambda w: f"Wallet_Analysis?wallet={quote_plus(str(w))}&chain={chain_param}"
			)
			display_df = display_df.rename(
				columns={
					"24h Txns": "24h Transactions",
					"Counterparties": "24h Counterparties",
				}
			)
			display_df = display_df.set_index("Rank")
			display_df.index.name = "#"

			st.dataframe(
				display_df,
				hide_index=False,
				use_container_width=True,
				column_config={
					"Wallet": st.column_config.LinkColumn(
						"Wallet",
						display_text=r"wallet=([^&]+)",
						width="medium",
					),
					"Priority Score": st.column_config.ProgressColumn(
						"Priority Score",
						min_value=0,
						max_value=100,
						format="%.1f",
					),
					"24h Volume": st.column_config.NumberColumn("24h Volume", format="$%.2f"),
					"24h Transactions": st.column_config.NumberColumn("24h Transactions", format="%d"),
					"24h Counterparties": st.column_config.NumberColumn("24h Counterparties", format="%d"),
				},
			)
			_force_same_tab_wallet_links()
		else:
			st.info("No wallet data available")

with tab3:
	with st.container(border=True):
		st.subheader("Stablecoin volume over time")

		timeseries_df = get_timeseries_data_chain(chain=chain, hours=selected_hours)
		
		if timeseries_df is not None and not timeseries_df.empty:
			fig_vol = create_volume_time_chart(timeseries_df, color_map=token_color_map)
			st.plotly_chart(fig_vol, use_container_width=True)
		else:
			st.info("No timeseries data available")

with tab4:
	with st.container(border=True):
		st.subheader("Total volume by token")
		if token_df is not None and not token_df.empty:
			fig_token = create_token_volume_chart(token_df)
			st.plotly_chart(fig_token, use_container_width=True)
		else:
			st.info("No token data available")

