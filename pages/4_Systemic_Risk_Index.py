import streamlit as st
from utils.sidebar import sidebar

data_source = sidebar()

st.title("Systemic Risk Index")
st.caption(
	"Advanced metrics for monitoring systemic risk across the stablecoin ecosystem. "
	"This page aggregates market-wide indicators to identify potential vulnerabilities."
)

with st.container(border=True):
	st.subheader("Coming Soon")
	st.info(
		"This page will feature:\n"
		"- Market concentration metrics\n"
		"- Cross-token risk correlations\n"
		"- Network-level vulnerability indicators\n"
		"- Systemic exposure heatmaps"
	)
