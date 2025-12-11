import streamlit as st
from utils.load_data import get_last_updated
from utils.sidebar import sidebar
from utils.styling import inject_icon_styles

inject_icon_styles()

last_updated = get_last_updated()
sidebar(last_updated)

st.title("Methodology")
st.caption("Analytical framework for identifying high-risk wallet behavior, detecting sanctions exposure, and quantifying systemic risk patterns within major stablecoin networks.")

with st.container(border=True):
	st.subheader("Methodology Overview")
	st.markdown(
		"""
	This document outlines the analytical framework used by StablecoinRiskMonitor to identify high-risk wallet behavior, 
	detect exposure to sanctioned entities, and quantify systemic-risk patterns within major stablecoin networks.
	
	The methodology is designed to provide **transparency, reproducibility, and public-benefit insights** that support 
	financial integrity and AML monitoring.
	"""
	)

with st.container(border=True):
	st.subheader("Data Ingestion")
	st.markdown(
		"""
	- Stablecoin transfer data is sourced from major blockchain networks
	- Transactions are aggregated at the wallet level to construct longitudinal behavioral profiles
	- All wallet addresses are anonymized to preserve privacy
	- Data updates occur every 24 hours through an automated processing pipeline
	- Sanctions lists are matched against public OFAC data
	- Pre-aggregated analytics are served via secure API endpoints to ensure fast dashboard performance
	"""
	)

with st.container(border=True):
	st.subheader("Metric Categories")
	st.markdown(
		"""
	The platform evaluates each wallet using multiple independent categories of risk indicators:
	
	### Transaction Volume
	Measures the scale and frequency of transfers. Higher volume may indicate greater exposure risk, 
	particularly when combined with velocity and clustering patterns.
	
	### Token Risk Profile
	Different stablecoins carry different risk characteristics based on issuer transparency, chain usage patterns, 
	and historical exposure levels. A token-specific factor adjusts the baseline risk of the wallet.
	
	### Wallet Concentration
	Measures how activity is distributed across counterparties. High concentration may indicate funneling, layering, 
	or single-source dependency—traits observed in prior AML cases.
	
	### Velocity and Movement Patterns
	Evaluates how quickly funds move through the wallet. Higher velocity suggests rapid transmission behavior 
	commonly associated with obfuscation or layering strategies.
	
	### Burst Activity
	Identifies short-interval clusters of transactions. Sudden activity spikes may indicate attempts to rapidly 
	move funds after receiving flagged or high-risk assets.
	
	### Temporal Spread
	Measures distribution of activity over a 24-hour window. Consistent irregular time patterns may correlate 
	with automated laundering, mixers, or bot-driven flows.
	
	### Sanctions Exposure
	Wallets that interact with addresses linked to sanctions lists receive an amplified risk multiplier. 
	The system does not label a wallet as sanctioned but adjusts risk indicators for analytical transparency.
	"""
	)

with st.container(border=True):
	st.subheader("Risk Score Construction")
	st.markdown(
		"""
	Each wallet receives a composite risk score between **0 and 100**.
	
	Scores are calculated using a proprietary weighted aggregation of the metric categories described above. 
	The scoring algorithm combines:
	
	- **Volume indicators** scaled logarithmically to measure systemic importance without overweighting large exchanges
	- **Concentration metrics** based on transaction size distribution patterns (Herfindahl index) weighted by volume significance
	- **Behavioral patterns** including velocity, burst activity, and temporal spread
	- **Token-specific risk factors** reflecting issuer and usage characteristics
	- **Sanctions exposure amplification** applied when interactions with sanctioned addresses are detected
	
	The weighting structure emphasizes concentration and behavioral anomalies while balancing contextual factors. 
	Sanctions exposure triggers multiplicative risk adjustment scaled by transaction volume to prioritize 
	material exposure cases.
	
	Specific weights and formulas are proprietary to maintain scoring integrity and prevent gaming, but the 
	underlying methodology follows established AML risk assessment frameworks.
	"""
	)

with st.container(border=True):
	st.subheader("Systemic-Risk Index")
	st.markdown(
		"""
	In addition to wallet-level scoring, StablecoinRiskMonitor computes a macro-level **Systemic-Risk Index** 
	that identifies broader stress conditions within stablecoin ecosystems by tracking:
	
	- Volume surges
	- Risk score clustering
	- Cross-stablecoin flow shifts
	- Concentration across major wallets
	- Expansion or contraction of high-risk segments
	
	The index is intended to support researchers and institutions in understanding emerging risk conditions 
	at a sector-wide level.
	"""
	)

with st.container(border=True):
	st.subheader("Design Principles")
	st.markdown(
		"""
	The methodology follows five core principles:
	
	1. **Transparency:** Metric categories and analytical approach are documented while protecting scoring integrity
	2. **Data Quality:** All analysis is based on blockchain data and verified sanctions lists
	3. **Independence:** Does not rely on non-verifiable sources or subjective classification
	4. **Public Benefit:** Improves visibility into AML and systemic-risk patterns
	5. **Privacy Protection:** Wallet identifiers remain anonymized
	"""
	)

with st.container(border=True):
	st.subheader("Disclaimer")
	st.markdown(
		"""
	StablecoinRiskMonitor provides **analytical indicators only**. It does not classify any entity as illicit, 
	sanctioned, or criminal. All outputs support research, transparency, and financial-integrity monitoring.
	
	This platform is intended to advance blockchain risk transparency and support compliance investigation, 
	regulatory oversight, and public-interest financial safety.
	"""
	)
