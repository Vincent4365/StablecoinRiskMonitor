import streamlit as st
from utils.load_data import load_cloud_data
from utils.sidebar import sidebar
from utils.formatting import format_volume, get_wallet_aggregation
from utils.charts import create_volume_time_chart, create_token_volume_chart
from utils.styling import inject_icon_styles

st.set_page_config(
	page_title="Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()

sidebar()

st.title("Stablecoin Risk Monitor")

# Left-side data snapshot caption just below the title
if "cloud_last_modified" in st.session_state:
	ts_str = st.session_state["cloud_last_modified"]
	# Place on the left under the title for immediate context.
	# Give the left column more width so the caption doesn't wrap onto multiple lines.
	col1, col2 = st.columns([3, 1])
	with col1:
		# Use the material time icon to match project icon style
		st.caption(f":material/access_time: Data Snapshot: {ts_str} (updated every 24 hours)")

# Cloud-only mode: always load pre-processed CSV from GCS
df = load_cloud_data()

if df.empty:
	st.info("No data available.")
	st.stop()

# Data info: the last-updated caption is shown below the volume chart

wallet_agg = get_wallet_aggregation(df)

total_volume = df["Volume"].sum()
total_transactions = len(df)

with st.container(border=True):
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Total Volume", format_volume(total_volume))
	with col2:
		st.metric("Unique Wallets", f"{df['Wallet'].nunique():,}")
	with col3:
		st.metric("Average Risk Score", f"{df['Risk Score'].mean():.1f}")
	with col4:
		st.metric("Total Transactions", f"{total_transactions:,}")

tab1, tab2, tab3 = st.tabs([
	":material/warning: High-Risk Wallets",
	":material/show_chart: Volume Over Time", 
	":material/bar_chart: Volume by Token"
])

with tab1:
	with st.container(border=True):
		st.subheader("Top 10 High-Risk Wallets")

		top_n = 10
		top_wallets = wallet_agg.head(top_n)

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
		if st.button("View expanded list"):
			st.switch_page("pages/2_Risk_Alerts.py")

with tab2:
	with st.container(border=True):
		st.subheader("Stablecoin volume over time")

		fig_vol = create_volume_time_chart(df)
		st.plotly_chart(fig_vol, use_container_width=True)

		# Show only the cloud CSV last-updated timestamp (if available)
		if 'cloud_last_modified' in st.session_state:
			# Use the material time icon to match the app's icon style instead of an emoji
			st.caption(f":material/access_time: Last updated: {st.session_state['cloud_last_modified']}")

with tab3:
	with st.container(border=True):
		st.subheader("Total volume by token")

		fig_token = create_token_volume_chart(df)
		st.plotly_chart(fig_token, use_container_width=True)

