import streamlit as st
from utils.load_data import load_demo_data, load_real_data
import plotly.express as px
from utils.sidebar import sidebar

st.set_page_config(
	page_title="Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

data_source = sidebar()

st.title("Stablecoin Risk Monitor")


st.markdown(
	"""
This app is a prototype dashboard for monitoring stablecoin activity and AML-related risk signals. All blockchain addresses have been anonymized, ensuring no personally identifiable wallet data is included.
"""
)

st.title("Overview")

if data_source.startswith("Demo"):
	df = load_demo_data()
else:
	df = load_real_data()

# Use new column names after renaming
# 'Risk Score', 'Volume', 'Wallet', 'Token', 'Date'
df_sorted = df.sort_values("Risk Score", ascending=False)
df_preview = df_sorted.head(1000)

st.subheader(f"Top 1000 rows from {data_source}")
st.dataframe(df_preview)

st.subheader("Key figures")

col1, col2, col3 = st.columns(3)
with col1:
	st.metric("Total volume (USD)", f"${df['Volume'].sum():,.0f}")
with col2:
	st.metric("Number of wallets", df["Wallet"].nunique())
with col3:
	st.metric("Average public risk score", f"{df['Risk Score'].mean():.1f}")

st.subheader("Stablecoin volume over time")

daily = df.groupby(["Date", "Hour", "Token"], as_index=False)["Volume"].sum()

fig_vol = px.line(
    daily,
    x="Hour",
    y="Volume",
    color="Token",
    line_group="Date",
    markers=False,
)
st.plotly_chart(fig_vol, use_container_width=True)

st.subheader("Total volume by token")

vol_token = df.groupby("Token", as_index=False)["Volume"].sum()
vol_token = vol_token.sort_values("Volume", ascending=True)
fig_token = px.bar(
    vol_token,
    x="Volume",
    y="Token",
    orientation="h",
    text="Volume",
)

fig_token.update_traces(texttemplate="%{text:,.0f}")
st.plotly_chart(fig_token, use_container_width=True)

