import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.sidebar import sidebar
from utils.styling import inject_icon_styles
from utils.formatting import (
	format_volume,
	format_relative_time,
	format_utc_timestamp,
	utc_now_timestamp,
)
from utils.load_data_new import (
	get_lookup_priority_distribution_chain,
	get_lookup_component_averages_chain,
	get_rolling_metrics_snapshot_raw,
)
from utils.load_data import get_top_counterparties


st.set_page_config(
	page_title="Advanced Analysis - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()


def _chain_param_from_ui(chain_label: str) -> str:
	return "Tron" if str(chain_label or "").strip().lower() == "tron" else "Ethereum"


def _set_session_value(key: str, value: str) -> None:
	st.session_state[key] = value


def _best_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
	for c in candidates:
		if c in df.columns:
			return c
	return None


COMPONENT_LABELS: dict[str, str] = {
	"priority_score": "Priority Score",
	"volume_score": "Transaction Volume",
	"velocity_score": "Activity / Velocity",
	"time_score": "Time Pattern",
	"burst_score": "Burstiness",
	"surge_score": "Surge / Reactivation",
	"sanctions_score": "Sanctions Intensity",
	"hhi_counterparty_score": "Counterparty Concentration (HHI)",
	"hhi_txn_size_score": "Txn Size Concentration (HHI)",
	"churn_score": "Counterparty Churn",
	# Legacy/alternate names that may appear in some snapshots
	"hhi_score": "HHI (Legacy)",
}


PREFERRED_COMPONENT_ORDER: list[str] = [
	"volume_score",
	"velocity_score",
	"time_score",
	"burst_score",
	"surge_score",
	"sanctions_score",
	"hhi_counterparty_score",
	"hhi_txn_size_score",
	"churn_score",
	"hhi_score",
]


def _get_component_columns(df: pd.DataFrame) -> list[str]:
	preferred = [c for c in PREFERRED_COMPONENT_ORDER if c in df.columns]
	others = [
		c
		for c in df.columns
		if str(c).endswith("_score") and c not in preferred and c != "priority_score"
	]
	others = sorted(others)
	return preferred + others

# Priority Scores
header_left, header_right = st.columns([4, 2], vertical_alignment="center")
with header_left:
	st.title("Advanced Analysis")

with header_right:
	if "chain" not in st.session_state:
		st.session_state["chain"] = "Ethereum"
	if "active_window" not in st.session_state:
		st.session_state["active_window"] = "24h"

with st.container(border=True):
	row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
	with row1_c1:
		prio_total_wallets_slot = st.empty()
	with row1_c2:
		prio_total_tx_slot = st.empty()
	with row1_c3:
		st.caption("Chain")
		c_eth, c_tron = st.columns(2, vertical_alignment="center")
		with c_eth:
			st.button(
				"Ethereum",
				key="chain_tile_eth",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") != "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Ethereum"),
			)
		with c_tron:
			st.button(
				"Tron",
				key="chain_tile_tron",
				use_container_width=True,
				type="primary" if st.session_state.get("chain", "Ethereum") == "Tron" else "secondary",
				on_click=_set_session_value,
				args=("chain", "Tron"),
			)
	with row1_c4:
		st.caption("Activity Window")
		w1, w2, w3 = st.columns(3, vertical_alignment="center")
		with w1:
			st.button(
				"24h",
				key="activity_tile_24h",
				use_container_width=True,
				type="primary" if st.session_state.get("active_window") == "24h" else "secondary",
				on_click=_set_session_value,
				args=("active_window", "24h"),
			)
		with w2:
			st.button(
				"7d",
				key="activity_tile_7d",
				use_container_width=True,
				type="primary" if st.session_state.get("active_window") == "7d" else "secondary",
				on_click=_set_session_value,
				args=("active_window", "7d"),
			)
		with w3:
			st.button(
				"30d",
				key="activity_tile_30d",
				use_container_width=True,
				type="primary" if st.session_state.get("active_window") == "30d" else "secondary",
				on_click=_set_session_value,
				args=("active_window", "30d"),
			)


# Fetch data AFTER controls so one click updates everything.
chain = _chain_param_from_ui(st.session_state.get("chain", "Ethereum"))
active_window = st.session_state.get("active_window", "24h")

dist_df, dist_asof_ts, dist_row_count = get_lookup_priority_distribution_chain(
	chain=chain,
	active_window=active_window,
)
avg_df, avg_asof_ts, avg_row_count = get_lookup_component_averages_chain(
	chain=chain,
	active_window=active_window,
)

# Also prefetch Advanced Analysis snapshot so the sidebar can show a single timestamp.
adv_df, adv_asof_ts = get_rolling_metrics_snapshot_raw(
	chain=chain,
	limit=1000,
	order_by="priority_score",
	order="desc",
)

asof_ts = dist_asof_ts or avg_asof_ts or adv_asof_ts
row_count = dist_row_count if dist_row_count is not None else avg_row_count

sidebar(last_updated=asof_ts, show_chain_toggle=False)


# Summary metric values
prio_total_tx_count = None
if dist_df is not None and not dist_df.empty and "total_tx_count" in dist_df.columns:
	val = pd.to_numeric(dist_df["total_tx_count"], errors="coerce")
	if val.notna().any():
		prio_total_tx_count = int(val.max())

prio_total_wallets_slot.metric(
	"Total Wallets",
	f"{int(row_count):,}" if row_count is not None else "Unknown",
)
prio_total_tx_slot.metric(
	"Transactions",
	f"{int(prio_total_tx_count):,}" if prio_total_tx_count is not None else "Unknown",
)


# Key metrics (used in Key metrics tab)
avg_priority = None
median_priority = None
min_priority = None
max_priority = None
total_volume_usd = None
sanctioned_wallet_count = None
total_sanctioned_volume_usd = None

if dist_df is not None and not dist_df.empty:
	for key, target in (
		("avg_priority_score", "avg"),
		("median_priority_score", "median"),
		("min_priority_score", "min"),
		("max_priority_score", "max"),
		("total_volume_usd", "vol"),
		("sanctioned_wallet_count", "sanctions_wallets"),
		("total_sanctioned_volume_usd", "sanctions_vol"),
	):
		if key in dist_df.columns:
			val = pd.to_numeric(dist_df[key], errors="coerce")
			if val.notna().any():
				if target == "avg":
					avg_priority = float(val.dropna().iloc[0])
				elif target == "median":
					median_priority = float(val.dropna().iloc[0])
				elif target == "min":
					min_priority = float(val.dropna().iloc[0])
				elif target == "max":
					max_priority = float(val.dropna().iloc[0])
				elif target == "vol":
					total_volume_usd = float(val.dropna().iloc[0])
				elif target == "sanctions_wallets":
					sanctioned_wallet_count = int(val.max())
				elif target == "sanctions_vol":
					total_sanctioned_volume_usd = float(val.dropna().iloc[0])

# Fallback avg from component-averages export.
if (
	avg_priority is None
	and avg_df is not None
	and not avg_df.empty
	and "component" in avg_df.columns
	and "avg_score" in avg_df.columns
):
	priority_rows = avg_df.loc[avg_df["component"].astype(str) == "priority_score"]
	if not priority_rows.empty:
		avg_priority = pd.to_numeric(priority_rows.iloc[0]["avg_score"], errors="coerce")
		if pd.notna(avg_priority):
			avg_priority = float(avg_priority)

# Fallback max from histogram bins if summary isn't present yet.
if (
	max_priority is None
	and dist_df is not None
	and not dist_df.empty
	and all(c in dist_df.columns for c in ("bin_start", "bin_end", "wallet_count"))
):
	_tmp = dist_df[["bin_start", "bin_end", "wallet_count"]].copy()
	_tmp["bin_start"] = pd.to_numeric(_tmp["bin_start"], errors="coerce")
	_tmp["bin_end"] = pd.to_numeric(_tmp["bin_end"], errors="coerce")
	_tmp["wallet_count"] = pd.to_numeric(_tmp["wallet_count"], errors="coerce")
	_tmp = _tmp.dropna(subset=["bin_start", "bin_end", "wallet_count"], how="any")
	_tmp = _tmp.loc[_tmp["wallet_count"] > 0]
	if not _tmp.empty:
		max_bin = _tmp.sort_values(["bin_end"], ascending=True).iloc[-1]
		max_priority = (float(max_bin["bin_start"]) + float(max_bin["bin_end"])) / 2.0


tab_distribution, tab_key_metrics, tab_components = st.tabs(
	[
		":material/query_stats: Priority Distribution",
		":material/table_chart: Key metrics",
		":material/show_chart: Average component scores",
	]
)

with tab_distribution:
	with st.container(border=True):
		st.subheader("Priority score distribution")
		if dist_df is None or dist_df.empty:
			st.info("No distribution data available")
		else:
			plot_df = dist_df.copy()
			for c in ("bin_start", "bin_end", "wallet_count"):
				if c in plot_df.columns:
					plot_df[c] = pd.to_numeric(plot_df[c], errors="coerce")
			plot_df = plot_df.dropna(subset=["bin_start", "bin_end", "wallet_count"], how="any")
			plot_df["bin_start"] = plot_df["bin_start"].astype(int)
			plot_df["bin_end"] = plot_df["bin_end"].astype(int)

			bins = pd.DataFrame({"bin_start": list(range(0, 100, 4))})
			bins["bin_end"] = bins["bin_start"] + 4
			plot_df = bins.merge(
				plot_df[["bin_start", "bin_end", "wallet_count"]],
				on=["bin_start", "bin_end"],
				how="left",
			)
			plot_df["wallet_count"] = plot_df["wallet_count"].fillna(0).astype(int)
			plot_df["Priority Score"] = (plot_df["bin_start"] + plot_df["bin_end"]) / 2

			fig = go.Figure()
			fig.add_trace(
				go.Bar(
					x=plot_df["Priority Score"],
					y=plot_df["wallet_count"],
					marker={
						"color": plot_df["Priority Score"],
						"colorscale": "RdYlGn_r",
						"cmin": 0,
						"cmax": 100,
						"showscale": False,
					},
					hovertemplate="Priority score: %{x:.0f}<br>Wallets: %{y:,}<extra></extra>",
				)
			)

			y_max = int(plot_df["wallet_count"].max()) if not plot_df.empty else 0
			y_line = max(1, y_max)
			cutoffs = [
				(30, "yellow", "Low/Medium"),
				(60, "orange", "Medium/High"),
				(80, "red", "High/Critical"),
			]
			for x, color, label in cutoffs:
				fig.add_trace(
					go.Scatter(
						x=[x, x],
						y=[0, y_line],
						mode="lines",
						line={"color": color, "width": 2, "dash": "dot"},
						hoverinfo="skip",
						showlegend=False,
					)
				)
				fig.add_annotation(
					x=x,
					y=y_line * 0.98,
					xref="x",
					yref="y",
					text=label,
					showarrow=False,
					font={"color": color},
					yanchor="bottom",
				)

			fig.update_layout(
				title_text="",
				xaxis_title="Priority score",
				yaxis_title="Number of wallets",
				showlegend=False,
				hovermode="x",
				height=360,
				margin={"l": 60, "r": 20, "t": 10, "b": 45},
			)
			fig.update_xaxes(range=[0, 100], tick0=0, dtick=10)
			if y_max > 0:
				fig.update_yaxes(range=[0, y_max * 1.1])
			st.plotly_chart(fig, use_container_width=True, key=f"risk_dist_{chain}_{active_window}")

			total_wallets = int(plot_df["wallet_count"].sum())
			low = int(plot_df.loc[plot_df["bin_start"] < 30, "wallet_count"].sum())
			med = int(
				plot_df.loc[(plot_df["bin_start"] >= 30) & (plot_df["bin_start"] < 60), "wallet_count"].sum()
			)
			high = int(
				plot_df.loc[(plot_df["bin_start"] >= 60) & (plot_df["bin_start"] < 80), "wallet_count"].sum()
			)
			crit = int(plot_df.loc[plot_df["bin_start"] >= 80, "wallet_count"].sum())

			low_pct = (low / total_wallets * 100) if total_wallets > 0 else 0.0
			med_pct = (med / total_wallets * 100) if total_wallets > 0 else 0.0
			high_pct = (high / total_wallets * 100) if total_wallets > 0 else 0.0
			crit_pct = (crit / total_wallets * 100) if total_wallets > 0 else 0.0

			c1, c2, c3, c4 = st.columns(4)
			c1.metric("Low Priority (0-30)", f"{low:,}", f"{low_pct:.1f}%")
			c2.metric("Medium Priority (30-60)", f"{med:,}", f"{med_pct:.1f}%")
			c3.metric("High Priority (60-80)", f"{high:,}", f"{high_pct:.1f}%")
			c4.metric("Critical Priority (80-100)", f"{crit:,}", f"{crit_pct:.1f}%")

with tab_key_metrics:
	with st.container(border=True):
		st.subheader("Key metrics")
		rows: list[dict[str, str]] = []
		rows.append({"Metric": "Chain", "Value": str(st.session_state.get("chain", "Ethereum"))})
		rows.append({"Metric": "Active timeframe", "Value": str(active_window)})
		if asof_ts:
			rows.append({"Metric": "Snapshot taken", "Value": format_relative_time(asof_ts, fallback=str(asof_ts))})
			rows.append({"Metric": "Snapshot (UTC)", "Value": format_utc_timestamp(asof_ts, fallback=str(asof_ts))})
			rows.append({"Metric": "Now (UTC)", "Value": utc_now_timestamp()})
		rows.append({"Metric": "Min transaction size", "Value": "$10"})
		rows.append({"Metric": "Min wallet volume (30d)", "Value": "$10,000"})
		rows.append({"Metric": "Total wallets", "Value": f"{int(row_count):,}" if row_count is not None else "Unknown"})
		rows.append({"Metric": "Transactions", "Value": f"{int(prio_total_tx_count):,}" if prio_total_tx_count is not None else "Unknown"})
		rows.append({"Metric": "Total volume", "Value": format_volume(float(total_volume_usd)) if total_volume_usd is not None and pd.notna(total_volume_usd) else "Unknown"})
		rows.append({"Metric": "Max priority score", "Value": f"{float(max_priority):.2f}" if max_priority is not None and pd.notna(max_priority) else "Unknown"})
		rows.append({"Metric": "Avg priority score", "Value": f"{float(avg_priority):.2f}" if avg_priority is not None and pd.notna(avg_priority) else "Unknown"})
		rows.append({"Metric": "Median priority score", "Value": f"{float(median_priority):.2f}" if median_priority is not None and pd.notna(median_priority) else "Unknown"})
		if min_priority is not None and pd.notna(min_priority):
			rows.append({"Metric": "Min priority score", "Value": f"{float(min_priority):.2f}"})
		rows.append({"Metric": "Sanctioned wallets", "Value": f"{int(sanctioned_wallet_count):,}" if sanctioned_wallet_count is not None else "Unknown"})
		rows.append({"Metric": "Sanctioned volume (30d)", "Value": format_volume(float(total_sanctioned_volume_usd)) if total_sanctioned_volume_usd is not None and pd.notna(total_sanctioned_volume_usd) else "Unknown"})

		metrics_df = pd.DataFrame(rows, columns=["Metric", "Value"])
		st.dataframe(
			metrics_df,
			hide_index=True,
			use_container_width=True,
			column_config={
				"Metric": st.column_config.TextColumn("Metric"),
				"Value": st.column_config.TextColumn("Value"),
			},
		)

with tab_components:
	with st.container(border=True):
		st.subheader("Average component scores")
		label_by_component = {
			"priority_score": "Priority Score",
			"volume_score": "Transaction Volume",
			"velocity_score": "Activity / Velocity",
			"time_score": "Time Pattern",
			"burst_score": "Burstiness",
			"surge_score": "Surge / Reactivation",
			"sanctions_score": "Sanctions Intensity",
			"hhi_counterparty_score": "Counterparty Concentration (HHI)",
			"hhi_txn_size_score": "Txn Size Concentration (HHI)",
			"churn_score": "Counterparty Churn",
		}
		preferred_order = [
			"priority_score",
			"volume_score",
			"velocity_score",
			"time_score",
			"burst_score",
			"surge_score",
			"sanctions_score",
			"hhi_counterparty_score",
			"hhi_txn_size_score",
			"churn_score",
		]

		if avg_df is None or avg_df.empty:
			st.info("No component average data available")
		else:
			view = avg_df.copy()
			if "component" in view.columns:
				view["Component"] = view["component"].astype(str).map(label_by_component).fillna(view["component"].astype(str))
			else:
				view["Component"] = "Unknown"
			if "avg_score" in view.columns:
				view["Avg Score"] = pd.to_numeric(view["avg_score"], errors="coerce")
			else:
				view["Avg Score"] = None

			order_map = {k: i for i, k in enumerate(preferred_order)}
			if "component" in view.columns:
				view["_order"] = view["component"].astype(str).map(order_map).fillna(999)
				view = view.sort_values(["_order", "Component"], ascending=[True, True])
				view = view.drop(columns=["_order"])
			else:
				view = view.sort_values(["Component"], ascending=True)

			view = view[["Component", "Avg Score"]]
			st.dataframe(
				view,
				hide_index=True,
				use_container_width=True,
				column_config={
					"Avg Score": st.column_config.NumberColumn("Avg Score", format="%.2f"),
				},
			)


# Advanced Analysis
st.divider()

adv_header_left, adv_header_right = st.columns([4, 2], vertical_alignment="center")
with adv_header_left:
	st.header("Top 1000 Analysis")
with adv_header_right:
	if "chain" not in st.session_state:
		st.session_state["chain"] = "Ethereum"

if adv_df is None or adv_df.empty:
	st.info("No data available for Advanced Analysis.")
else:
	df = adv_df

	with st.container(border=True):
		row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
		with row1_c1:
			adv_total_wallets_slot = st.empty()
		with row1_c2:
			adv_avg_score_slot = st.empty()
		with row1_c3:
			adv_max_score_slot = st.empty()
		with row1_c4:
			st.caption("Chain")
			c_eth, c_tron = st.columns(2, vertical_alignment="center")
			with c_eth:
				st.button(
					"Ethereum",
					key="adv_chain_tile_eth",
					use_container_width=True,
					type="primary" if st.session_state.get("chain", "Ethereum") != "Tron" else "secondary",
					on_click=_set_session_value,
					args=("chain", "Ethereum"),
				)
			with c_tron:
				st.button(
					"Tron",
					key="adv_chain_tile_tron",
					use_container_width=True,
					type="primary" if st.session_state.get("chain", "Ethereum") == "Tron" else "secondary",
					on_click=_set_session_value,
					args=("chain", "Tron"),
				)

	priority_col = _best_col(df, ["priority_score", "priority_score_24h"]) or "priority_score"

	tab_components, tab_category, tab_concentration, tab_activity, tab_top_addresses = st.tabs(
		[
			":material/show_chart: Component analysis",
			":material/table_chart: Category breakdown",
			":material/query_stats: Concentration (HHI)",
			":material/timeline: Activity & velocity",
			":material/table_view: Top addresses",
		]
	)

	with tab_components:
		with st.container(border=True):
			st.subheader("Risk component analysis")

			component_cols = _get_component_columns(df)
			if not component_cols:
				st.warning("Component score data not available")
			else:
				avg_scores = df[component_cols].apply(pd.to_numeric, errors="coerce").mean()
				component_data = pd.DataFrame(
					{
						"component": avg_scores.index.astype(str),
						"Component": [COMPONENT_LABELS.get(str(c), str(c)) for c in avg_scores.index.astype(str)],
						"Average Score": avg_scores.values,
					}
				)
				component_data = component_data.sort_values(["Average Score"], ascending=False)

				fig = px.bar(
					component_data,
					x="Component",
					y="Average Score",
					title="Average scores by component",
					color="Average Score",
					color_continuous_scale="Reds",
					text="Average Score",
				)
				fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
				fig.update_layout(
					xaxis_title="",
					yaxis_title="Average Score",
					showlegend=False,
					yaxis_range=[0, 100],
				)
				st.plotly_chart(fig, use_container_width=True)

				st.subheader("Component contribution to final priority score")
				p = pd.to_numeric(df.get(priority_col), errors="coerce")
				correlations = []
				for col in component_cols:
					c = pd.to_numeric(df[col], errors="coerce").corr(p)
					correlations.append(c)

				corr_data = pd.DataFrame(
					{
						"component": [str(c) for c in component_cols],
						"Component": [COMPONENT_LABELS.get(str(c), str(c)) for c in component_cols],
						"Correlation": correlations,
					}
				)
				corr_data = corr_data.sort_values(["Correlation"], ascending=False)
				fig = px.bar(
					corr_data,
					x="Component",
					y="Correlation",
					title="Correlation with priority score",
					color="Correlation",
					color_continuous_scale="RdYlGn_r",
					text="Correlation",
				)
				fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
				fig.update_layout(
					xaxis_title="",
					yaxis_title="Correlation",
					showlegend=False,
					yaxis_range=[-1, 1],
				)
				st.plotly_chart(fig, use_container_width=True)

	with tab_category:
		with st.container(border=True):
			st.subheader("Average component scores by risk category")

			component_cols = _get_component_columns(df)
			if not component_cols:
				st.warning("Component score data not available for detailed breakdown")
			else:
				view = df.copy()
				p = pd.to_numeric(view.get(priority_col), errors="coerce")
				view = view.loc[p.notna()].copy()
				view["__priority"] = p.loc[view.index]

				view["risk_category"] = pd.cut(
					view["__priority"],
					bins=[0, 30, 60, 80, 100],
					labels=["Low (0-30)", "Medium (30-60)", "High (60-80)", "Critical (80-100)"],
				)
				view["risk_category"] = view["risk_category"].cat.set_categories(
					["Low (0-30)", "Medium (30-60)", "High (60-80)", "Critical (80-100)"],
					ordered=True,
				)

				category_stats = view.groupby("risk_category", observed=False)[component_cols].apply(
					lambda x: x.apply(pd.to_numeric, errors="coerce").mean()
				)
				category_stats = category_stats.reset_index().rename(columns={"risk_category": "Risk Category"})
				category_stats = category_stats.rename(columns={c: COMPONENT_LABELS.get(c, c) for c in component_cols})
				ordered_cols = ["Risk Category"] + [c for c in category_stats.columns if c != "Risk Category"]
				category_stats = category_stats[ordered_cols]

				column_config: dict[str, object] = {"Risk Category": st.column_config.TextColumn("Risk Category")}
				for c in category_stats.columns:
					if c == "Risk Category":
						continue
					column_config[c] = st.column_config.NumberColumn(c, format="%.2f")
				st.dataframe(
					category_stats,
					hide_index=True,
					use_container_width=True,
					column_config=column_config,
				)

	with tab_concentration:
		with st.container(border=True):
			st.subheader("Counterparty concentration analysis")

			hhi_cp = _best_col(df, ["hhi_counterparty_24h", "hhi_counterparty"])
			hhi_txn = _best_col(df, ["hhi_txn_size_24h", "hhi_txn_size"])

			if hhi_cp is None and hhi_txn is None:
				st.warning("HHI concentration metrics not available")
			else:
				if hhi_cp is not None:
					col1, col2 = st.columns(2)
					with col1:
						vals = pd.to_numeric(df[hhi_cp], errors="coerce").dropna()
						st.metric("Average HHI (24h)", "N/A" if vals.empty else f"{float(vals.mean()):.4f}")
						st.metric("Maximum HHI (24h)", "N/A" if vals.empty else f"{float(vals.max()):.4f}")
					with col2:
						fig = px.histogram(
							df,
							x=hhi_cp,
							nbins=30,
							title="HHI distribution (24h)",
							color_discrete_sequence=["#1f77b4"],
						)
						st.plotly_chart(fig, use_container_width=True)

				if hhi_txn is not None:
					col1, col2 = st.columns(2)
					with col1:
						vals = pd.to_numeric(df[hhi_txn], errors="coerce").dropna()
						st.metric("Average Txn Size HHI (24h)", "N/A" if vals.empty else f"{float(vals.mean()):.4f}")
						st.metric("Maximum Txn Size HHI (24h)", "N/A" if vals.empty else f"{float(vals.max()):.4f}")
					with col2:
						fig = px.histogram(
							df,
							x=hhi_txn,
							nbins=30,
							title="Transaction size HHI distribution (24h)",
							color_discrete_sequence=["#2ca02c"],
						)
						st.plotly_chart(fig, use_container_width=True)

	with tab_activity:
		with st.container(border=True):
			st.subheader("Activity and velocity patterns")

			tx_count = _best_col(df, ["tx_count_24h", "tx_count"])
			avg_interval = _best_col(df, ["avg_tx_interval_24h", "avg_tx_interval"])
			unique_cp = _best_col(df, ["unique_counterparties_24h", "unique_counterparties"])

			col1, col2 = st.columns(2)
			with col1:
				if avg_interval is not None:
					vals = pd.to_numeric(df[avg_interval], errors="coerce").dropna()
					st.metric("Average Transaction Interval (24h)", "N/A" if vals.empty else f"{float(vals.mean()):.0f}s")
				if tx_count is not None:
					vals = pd.to_numeric(df[tx_count], errors="coerce").dropna()
					st.metric("Average Transactions (24h)", "N/A" if vals.empty else f"{float(vals.mean()):.1f}")
					st.metric("Maximum Transactions (24h)", "N/A" if vals.empty else f"{int(vals.max()):,}")

			with col2:
				if unique_cp is not None:
					vals = pd.to_numeric(df[unique_cp], errors="coerce").dropna()
					st.metric("Average Counterparties (24h)", "N/A" if vals.empty else f"{float(vals.mean()):.1f}")
					st.metric("Maximum Counterparties (24h)", "N/A" if vals.empty else f"{int(vals.max()):,}")

	with tab_top_addresses:
		with st.container(border=True):
			col_title, col_ctrl = st.columns([3, 1], vertical_alignment="center")
			with col_title:
				st.subheader("Top Addresses by Unique Counterparties (24h)")
			with col_ctrl:
				label_col, select_col = st.columns([1, 3], vertical_alignment="center")
				with label_col:
					st.caption("Show")
				with select_col:
					top_n_options = [10, 25, 50, 100]
					current_top_n = int(st.session_state.get("adv_top_addresses_n", 10) or 10)
					top_n = st.selectbox(
						"Addresses to show",
						options=top_n_options,
						index=top_n_options.index(current_top_n) if current_top_n in top_n_options else 0,
						key="adv_top_addresses_n",
						label_visibility="collapsed",
					)

			chain_param = "tron" if st.session_state.get("chain", "Ethereum") == "Tron" else "eth"
			df_cp = get_top_counterparties(top_n=int(top_n), hours=24, chain=chain_param)
			if df_cp is None or df_cp.empty:
				st.info("No data available for this view.")
			else:
				out = pd.DataFrame()
				out["rank"] = range(1, len(df_cp) + 1)
				out["address"] = df_cp.get("address")
				out["total_counterparties"] = df_cp.get("total_counterparties")
				out["sending_counterparties"] = df_cp.get("sending_counterparties")
				out["receiving_counterparties"] = df_cp.get("receiving_counterparties")
				out["transactions"] = df_cp.get("transactions")
				out["total_volume"] = df_cp.get("total_volume")
				out["priority_score"] = df_cp.get("priority_score")
				out["label"] = df_cp.get("label")
				out["entity_type"] = df_cp.get("entity_type")

				st.dataframe(
					out,
					hide_index=True,
					use_container_width=True,
					column_config={
						"rank": st.column_config.NumberColumn("#", format="%d", width="small"),
						"address": st.column_config.TextColumn("Address", width="large"),
						"total_counterparties": st.column_config.NumberColumn(
							"Total Counterparties",
							format="%d",
							help="Unique counterparties in the last 24h (rolling)",
						),
						"sending_counterparties": st.column_config.NumberColumn(
							"Sending",
							format="%d",
							help="Unique recipients in last 24h (rolling)",
						),
						"receiving_counterparties": st.column_config.NumberColumn(
							"Receiving",
							format="%d",
							help="Unique senders in last 24h (rolling)",
						),
						"transactions": st.column_config.NumberColumn("Transactions", format="%d"),
						"total_volume": st.column_config.NumberColumn("Total Volume (USD)", format="%.2f"),
						"priority_score": st.column_config.NumberColumn("Priority Score", format="%.2f"),
						"label": st.column_config.TextColumn("Label", width="medium"),
						"entity_type": st.column_config.TextColumn("Entity Type", width="small"),
					},
				)

	# Keep Advanced Analysis summary slots populated after the fetch.
	adv_total_wallets_slot.metric("Top Priority Wallets", f"{len(df):,}")
	_avg = pd.to_numeric(df.get(priority_col), errors="coerce").dropna().mean()
	adv_avg_score_slot.metric("Avg Priority Score", "N/A" if pd.isna(_avg) else f"{float(_avg):.2f}")

	_max = pd.to_numeric(df.get(priority_col), errors="coerce").dropna().max()
	adv_max_score_slot.metric("Max Priority Score", "N/A" if pd.isna(_max) else f"{float(_max):.2f}")
