import streamlit as st
from utils.load_data import get_risk_distribution, get_component_scores, get_last_updated
from utils.sidebar import sidebar
from utils.charts import create_risk_histogram_from_api
from utils.styling import inject_icon_styles

inject_icon_styles()

last_updated = get_last_updated()
sidebar(last_updated)

st.title("Risk Scores")
st.caption(
	"This page shows the risk score (0–100) and its main components: "
	"transaction volume, token profile, wallet concentration, activity, and sanctions intensity."
)

default_tokens = ["USDT", "USDC", "DAI"]

risk_dist = get_risk_distribution()

if risk_dist.empty:
	st.info("No data available.")
	st.stop()

available_tokens = sorted(risk_dist["Token"].unique()) if "Token" in risk_dist.columns else default_tokens

tokens = st.multiselect(
	"Filter by token",
	available_tokens,
	default=available_tokens,
)

with st.container(border=True):
	st.subheader("Risk score distribution")
	
	risk_data = get_risk_distribution(tokens=tokens)
	
	if not risk_data.empty:
		fig_hist = create_risk_histogram_from_api(risk_data)
		st.plotly_chart(fig_hist, use_container_width=True)
	else:
		st.info("No risk distribution data available")

with st.container(border=True):
	st.subheader("Average component scores by token")
	
	comp = get_component_scores(tokens=tokens)
	
	if not comp.empty:
		st.dataframe(comp, hide_index=True, use_container_width=True)
	else:
		st.info("No component score data available")