import streamlit as st
from utils.load_data import load_demo_data, load_real_data
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

data_source = sidebar()

st.title("Stablecoin Risk Monitor")

if data_source.startswith("Demo"):
	df = load_demo_data()
else:
	df = load_real_data()

if df.empty:
	st.info("No data available.")
	st.stop()

wallet_agg = get_wallet_aggregation(df)

total_volume = df["Volume"].sum()
sanctioned_vol = df.loc[df["Sanctioned"] == 1, "Volume"].sum()
sanctioned_share = (sanctioned_vol / total_volume * 100) if total_volume > 0 else 0

with st.container(border=True):
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Total Volume", format_volume(total_volume))
	with col2:
		st.metric("Unique Wallets", f"{df['Wallet'].nunique():,}")
	with col3:
		st.metric("Average Risk Score", f"{df['Risk Score'].mean():.1f}")
	with col4:
		st.metric("Sanctioned Share", f"{sanctioned_share:.2f}%")

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

with tab3:
	with st.container(border=True):
		st.subheader("Total volume by token")

		fig_token = create_token_volume_chart(df)
		st.plotly_chart(fig_token, use_container_width=True)

