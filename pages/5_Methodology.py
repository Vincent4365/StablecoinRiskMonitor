import streamlit as st
from utils.sidebar import sidebar
from utils.styling import inject_icon_styles

inject_icon_styles()

data_source = sidebar()

st.title("Methodology")
st.caption("Explanation of risk scoring methodology and data sources used in this dashboard.")

with st.container(border=True):
	st.subheader("Risk Score Components")
	st.markdown(
		"""
	The public risk score (0-100) combines several components:
	
	- **Transaction Volume** (25%) - Size and frequency of transfers
	- **Token Profile** (20%) - Stablecoin type and contract characteristics
	- **Wallet Concentration** (20%) - How volume is distributed across wallets
	- **Velocity/Activity** (20%) - How quickly funds move through the wallet
	- **Burst Score** (10%) - Concentration of transactions in specific hours
	- **Time Activity** (5%) - Spread of activity across 24-hour periods
	
	**Sanctions Multiplier:** Wallets with sanctioned transactions receive a volume-based multiplier
	on their base score, scaling logarithmically with transaction amounts.
	"""
	)

with st.container(border=True):
	st.subheader("Data Privacy")
	st.markdown(
		"""
	All blockchain addresses are fully anonymized before analysis. No personally identifiable 
	wallet information is retained. Transaction data is aggregated at the wallet level with 
	anonymous identifiers.
	"""
	)
