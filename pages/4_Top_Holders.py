import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.sidebar import sidebar
from utils.formatting import format_volume_exact
from utils.styling import inject_icon_styles
from utils.load_data import get_eth_rich_list, get_tron_rich_list
from utils.load_data_new import get_last_updated

st.set_page_config(
	page_title="Top Holders - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()

# Token mapping
TOKEN_MAP = {
	"USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
	"USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
	"DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
	"USDE": "0x4c9edd5852cd905f086c759e8383e09bff1e68b3",
}


def _set_session_value(key: str, value: str) -> None:
	st.session_state[key] = value


if "top_holders_token" not in st.session_state:
	st.session_state["top_holders_token"] = "USDT"

selected_token = str(st.session_state.get("top_holders_token") or "USDT")
if selected_token not in TOKEN_MAP:
	selected_token = "USDT"
	st.session_state["top_holders_token"] = "USDT"

st.title(f"Top {selected_token} holders")
token_address = TOKEN_MAP[selected_token]

# Fetch data based on selected token
_fetch_slot = st.empty()
with _fetch_slot.container():
	with st.spinner(f"Loading {selected_token} holder data..."):
		if selected_token == "USDT":
			# Fetch both ETH and TRON for USDT (API is Parquet-backed; max 1,000 rows).
			eth_df = get_eth_rich_list(token_address, limit=1000)
			tron_df = get_tron_rich_list(limit=1000)
			data = pd.concat([eth_df, tron_df], ignore_index=True) if (not eth_df.empty or not tron_df.empty) else pd.DataFrame()
		else:
			# Other tokens: ETH only
			data = get_eth_rich_list(token_address, limit=1000)
_fetch_slot.empty()

df = data if isinstance(data, pd.DataFrame) else pd.DataFrame()

freshness_ts = None
if not df.empty:
	# Prefer snapshot timestamp (as-of hour) over last per-row balance change.
	if "asof_ts" in df.columns:
		asof = pd.to_datetime(df["asof_ts"], utc=True, errors="coerce")
		asof_nonnull = asof.dropna()
		if not asof_nonnull.empty:
			# If multiple chains are combined (USDT), show the oldest snapshot so both are covered.
			freshness_ts = asof_nonnull.min().strftime("%Y-%m-%dT%H:%M:%SZ")

	if freshness_ts is None and "updated_at" in df.columns:
		updated = pd.to_datetime(df["updated_at"], utc=True, errors="coerce")
		if updated.notna().any():
			freshness_ts = updated.max().strftime("%Y-%m-%dT%H:%M:%SZ")

sidebar(last_updated=freshness_ts or get_last_updated(chain="Ethereum"), show_chain_toggle=False)

# Prepare a stable, ranked DataFrame for display/analysis.
df_ranked = df.copy()
if not df_ranked.empty:
	# Add chain column if not present (for non-USDT tokens)
	if "chain" not in df_ranked.columns:
		df_ranked["chain"] = "Ethereum"
	# Sort by balance descending and add rank
	df_ranked = df_ranked.sort_values("balance", ascending=False).reset_index(drop=True)
	df_ranked.insert(0, "Rank", range(1, len(df_ranked) + 1))

# Display metrics (always render to keep UI stable)
metric_value = "—"
if not df_ranked.empty and "balance" in df_ranked.columns:
	metric_value = format_volume_exact(float(df_ranked["balance"].sum()))

with st.container(border=True):
	col_left, col_right = st.columns([2.4, 2.1], vertical_alignment="center")
	with col_left:
		st.metric("Total Balance (Top 1,000)", metric_value)
	with col_right:
		st.caption("Token")
		btn_cols = st.columns(4, vertical_alignment="center")
		for i, token in enumerate(TOKEN_MAP.keys()):
			with btn_cols[i]:
				st.button(
					token,
					key=f"top_holders_token_btn_{token}",
					use_container_width=True,
					type="primary" if selected_token == token else "secondary",
					on_click=_set_session_value,
					args=("top_holders_token", token),
				)

# Top-level tabs (always render to preserve tab selection across token changes)
tab_table, tab_wealth = st.tabs([
	":material/table_view: Top holders",
	":material/query_stats: Wealth distribution",
])

with tab_table:
	with st.container(border=True):
		col_title, col_ctrl = st.columns([3, 1], vertical_alignment="center")
		with col_title:
			st.subheader(f"Top {selected_token} holders")
		with col_ctrl:
			label_col, select_col = st.columns([1, 3], vertical_alignment="center")
			with label_col:
				st.caption("Show")
			with select_col:
				options = [10, 25, 50, 100, 250, 500, 1000]
				current = int(st.session_state.get("top_holders_show", 100) or 100)
				num_holders = st.selectbox(
					"Holders to show",
					options=options,
					index=options.index(current) if current in options else options.index(100),
					key="top_holders_show",
					label_visibility="collapsed",
				)

		if df_ranked.empty:
			st.info("No data available. Please check the API connection.")
		else:
			# Filter to top N holders
			df_display = df_ranked.head(int(num_holders))

			# Format display DataFrame
			display_df = df_display.copy()
			display_df["Balance"] = display_df["balance"].apply(format_volume_exact)
			display_df["Address"] = display_df["address"]
			display_df["Chain"] = display_df["chain"]

			# Show selected columns
			display_columns = ["Rank", "Chain", "Address", "Balance"]

			st.dataframe(
				display_df[display_columns],
				hide_index=True,
				use_container_width=True,
				column_config={
					"Rank": st.column_config.NumberColumn(
						"#",
						help="Holder rank by balance",
						format="%d",
						width="small",
					),
					"Chain": st.column_config.TextColumn(
						"Chain",
						help="Blockchain network",
						width="small",
					),
					"Address": st.column_config.TextColumn(
						"Wallet Address",
						help="Wallet address",
					),
					"Balance": st.column_config.TextColumn(
						"Balance",
						help="Token balance",
					),
				},
			)

with tab_wealth:
	with st.container(border=True):
		st.subheader(f"Wealth Distribution Analysis - {selected_token}")

		if df_ranked.empty:
			st.info("No data available. Please check the API connection.")
		else:
			# Filter positive balances and sort
			df_analysis = df_ranked[df_ranked["balance"] > 0].copy()
			df_analysis = df_analysis.sort_values("balance", ascending=True).reset_index(drop=True)

			total_supply = float(df_analysis["balance"].sum()) if not df_analysis.empty else 0.0
			num_holders = int(len(df_analysis))
			if num_holders == 0 or total_supply <= 0:
				st.info("Not enough positive-balance holders to compute distribution.")
			else:
				# Calculate cumulative values for Lorenz curve
				df_analysis["cumulative_holders_pct"] = (np.arange(1, num_holders + 1) / num_holders) * 100
				df_analysis["cumulative_supply_pct"] = (df_analysis["balance"].cumsum() / total_supply) * 100

				# Calculate Gini coefficient
				# Gini = (2 * sum(i * balance_i)) / (n * total_supply) - (n + 1) / n
				df_analysis["rank"] = np.arange(1, num_holders + 1)
				gini = (2 * (df_analysis["rank"] * df_analysis["balance"]).sum()) / (num_holders * total_supply) - (num_holders + 1) / num_holders

				# Calculate HHI (Herfindahl-Hirschman Index)
				df_analysis["share"] = df_analysis["balance"] / total_supply
				hhi = (df_analysis["share"] ** 2).sum()
				effective_holders = 1 / hhi if hhi > 0 else 0

				# Calculate top-N concentration
				df_sorted_desc = df_analysis.sort_values("balance", ascending=False).reset_index(drop=True)
				concentration_levels = [10, 50, 100, 1000]
				concentration_data = []
				for n in concentration_levels:
					if n <= num_holders:
						top_n_supply = df_sorted_desc.head(n)["balance"].sum()
						pct = (top_n_supply / total_supply) * 100
						concentration_data.append({"Level": f"Top {n}", "Percentage": pct})

				# Display metrics
				col1, col2, col3 = st.columns(3)
				with col1:
					st.metric("Gini Coefficient", f"{gini:.4f}")
				with col2:
					st.metric("HHI", f"{hhi:.6f}")
				with col3:
					st.metric("Effective Holders", f"{effective_holders:.0f}")

				# Tab layout for charts
				tab1, tab2 = st.tabs(["Lorenz Curve", "Top-N Concentration"])

				with tab1:
					fig_lorenz = go.Figure()
					fig_lorenz.add_trace(go.Scatter(
						x=df_analysis["cumulative_holders_pct"],
						y=df_analysis["cumulative_supply_pct"],
						mode="lines",
						name="Lorenz Curve",
						line=dict(color="blue", width=2),
					))
					fig_lorenz.add_trace(go.Scatter(
						x=[0, 100],
						y=[0, 100],
						mode="lines",
						name="Perfect Equality",
						line=dict(color="red", width=2, dash="dash"),
					))
					fig_lorenz.update_layout(
						title=f"Lorenz Curve - {selected_token}",
						xaxis_title="Cumulative % of Holders",
						yaxis_title="Cumulative % of Supply",
						height=500,
						hovermode="x unified",
					)
					st.plotly_chart(fig_lorenz, use_container_width=True)

				with tab2:
					if concentration_data:
						conc_df = pd.DataFrame(concentration_data)
						y_max = max(100.0, float(pd.to_numeric(conc_df["Percentage"], errors="coerce").max() or 0.0) + 5.0)
						fig_conc = go.Figure()
						fig_conc.add_trace(go.Bar(
							x=conc_df["Level"],
							y=conc_df["Percentage"],
							text=conc_df["Percentage"].apply(lambda x: f"{x:.2f}%"),
							textposition="outside",
							cliponaxis=False,
							marker_color="steelblue",
						))
						fig_conc.update_layout(
							title=f"Supply Concentration - {selected_token}",
							xaxis_title="Holder Group",
							yaxis_title="% of Total Supply",
							height=480,
							margin=dict(l=40, r=80, t=70, b=80),
							xaxis=dict(automargin=True, type="category"),
							yaxis=dict(range=[0, y_max]),
						)
						st.plotly_chart(fig_conc, use_container_width=True)
					else:
						st.info("No concentration data available.")
