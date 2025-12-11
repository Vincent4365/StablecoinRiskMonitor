import streamlit as st
from utils.load_data import get_dashboard_summary, get_top_wallets, get_timeseries_data, get_token_volume, get_last_updated
from utils.sidebar import sidebar
from utils.formatting import format_volume
from utils.charts import create_volume_time_chart, create_token_volume_chart
from utils.styling import inject_icon_styles

st.set_page_config(
	page_title="Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()

last_updated = get_last_updated()

sidebar(last_updated)

st.title("Stablecoin Risk Monitor")

# Initialize time range if not set
if "time_range" not in st.session_state:
	st.session_state["time_range"] = 24

# Get selected time range early for summary
selected_hours = st.session_state.get("time_range", 24)

summary = get_dashboard_summary(hours=selected_hours)

if not summary:
	st.info("No data available.")
	st.stop()

date_range = summary.get("date_range", {})
date_start = date_range.get("start", "N/A")
date_end = date_range.get("end", "N/A")

# Time range selector
st.markdown("**Show last:**")
col_a, col_b, col_c, col_d = st.columns([0.5, 0.5, 0.5, 4])
with col_a:
	if st.button("4h", use_container_width=True, type="primary" if st.session_state.get("time_range", 24) == 4 else "secondary"):
		st.session_state["time_range"] = 4
		st.rerun()
with col_b:
	if st.button("12h", use_container_width=True, type="primary" if st.session_state.get("time_range", 24) == 12 else "secondary"):
		st.session_state["time_range"] = 12
		st.rerun()
with col_c:
	if st.button("24h", use_container_width=True, type="primary" if st.session_state.get("time_range", 24) == 24 else "secondary"):
		st.session_state["time_range"] = 24
		st.rerun()

with st.container(border=True):
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Total Volume", format_volume(summary.get("total_volume", 0)))
	with col2:
		st.metric("Unique Wallets", f"{summary.get('unique_wallets', 0):,}")
	with col3:
		st.metric("Average Risk Score", f"{summary.get('average_risk_score', 0):.1f}")
	with col4:
		st.metric("Total Transactions", f"{summary.get('total_transactions', 0):,}")

tab1, tab2, tab3 = st.tabs([
	":material/warning: High-Risk Wallets",
	":material/show_chart: Volume Over Time", 
	":material/bar_chart: Volume by Token"
])

with tab1:
	with st.container(border=True):
		st.subheader("Top 10 High-Risk Wallets")

		top_wallets = get_top_wallets(top_n=10, sort_by='risk', hours=selected_hours)

		if not top_wallets.empty:
			st.dataframe(
				top_wallets[
					[
						"Wallet",
						"Total Volume",
						"Transactions",
						"Average Risk",
						"Max Risk",
						"Sanctioned Volume",
					]
				],
				hide_index=True,
				use_container_width=True
			)
		else:
			st.info("No wallet data available")
		
		if st.button("View expanded list"):
			st.switch_page("pages/2_Risk_Alerts.py")

with tab2:
	with st.container(border=True):
		st.subheader("Stablecoin volume over time")

		timeseries_df = get_timeseries_data(hours=selected_hours)
		
		if not timeseries_df.empty:
			fig_vol = create_volume_time_chart(timeseries_df)
			st.plotly_chart(fig_vol, use_container_width=True)
		else:
			st.info("No timeseries data available")

with tab3:
	with st.container(border=True):
		st.subheader("Total volume by token")

		token_df = get_token_volume(hours=selected_hours)
		
		if not token_df.empty:
			fig_token = create_token_volume_chart(token_df)
			st.plotly_chart(fig_token, use_container_width=True)
		else:
			st.info("No token data available")

