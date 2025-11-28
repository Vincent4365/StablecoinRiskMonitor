import streamlit as st
from utils.load_data import load_cloud_data
from utils.sidebar import sidebar
from utils.charts import create_risk_histogram, get_component_scores
from utils.styling import inject_icon_styles

inject_icon_styles()

sidebar()

st.title("Risk Scores")
st.caption(
	"This page shows the public risk score (0–100) and its main components: "
	"transaction volume, token profile, wallet concentration, activity, and sanctions intensity."
)

# Cloud-only dataset
df = load_cloud_data()

if df.empty:
	st.info("No data available.")
	st.stop()

tokens = st.multiselect(
	"Filter by token",
	sorted(df["Token"].unique()),
	default=sorted(df["Token"].unique()),
)

with st.container(border=True):
	st.subheader("Public risk score distribution")
	fig_hist = create_risk_histogram(df, tuple(tokens))
	st.plotly_chart(fig_hist, use_container_width=True)

with st.container(border=True):
	st.subheader("Average component scores by token")
	comp = get_component_scores(df, tuple(tokens))
	st.dataframe(comp, hide_index=True, use_container_width=True)