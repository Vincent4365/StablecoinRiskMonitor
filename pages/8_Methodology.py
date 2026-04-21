import streamlit as st
from utils.load_data_new import get_last_updated
from utils.sidebar import sidebar
from utils.styling import inject_icon_styles

st.set_page_config(
	page_title="Methodology - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()

last_updated = get_last_updated()
sidebar(last_updated)

st.title("Methodology")
st.caption(
	"Analytical framework for prioritizing wallets for investigation, monitoring sanctions-linked exposure, "
	"and quantifying systemic risk patterns within major stablecoin networks."
)

with st.container(border=True):
	st.subheader("Methodology Overview")
	st.markdown(
		"""
	This document outlines the analytical framework used by StablecoinRiskMonitor to prioritize wallets for analysis,
	detect exposure to sanctioned entities, and quantify systemic-risk patterns within major stablecoin networks.
	
	The methodology is designed to provide **transparency, reproducibility, and public-benefit insights** that support 
	financial integrity and AML monitoring.
	"""
	)

with st.container(border=True):
	st.subheader("Data Ingestion")
	st.markdown(
		"""
	- Stablecoin transfer data is sourced from major blockchain networks (Ethereum + Tron).
	- Only transactions above $10 USD are included to reduce noise and focus on material activity.
	- Transfers are aggregated at the wallet level to construct longitudinal behavioral profiles.
	- Refresh cadence varies by dataset:
		- Wallet-level priority snapshots are generated on a scheduled batch cadence.
		- The Systemic-Risk Index is computed from an hourly aggregated stablecoin snapshot.
	- Sanctions inputs originate from OFAC SDN, with the pipeline consuming a project-maintained resolved address list.
	- Pre-aggregated analytics are served via API endpoints for fast dashboard performance.
	"""
	)

with st.container(border=True):
	st.subheader("Metric Categories")
	st.markdown(
		"""
	The platform evaluates each wallet using multiple independent categories of signals to **prioritize** wallets for follow-up analysis.
	These signals are not, by themselves, a determination of illicit behavior.
	
	### Transaction Volume
	Measures the scale and frequency of transfers. Higher volume can increase monitoring priority,
	particularly when combined with rapid movement or concentration patterns.

	### Counterparty Concentration (HHI)
	Measures how concentrated activity is across counterparties. High concentration can indicate funneling, layering,
	or single-source dependency—patterns that can warrant closer review in AML workflows.

	### Txn Size Concentration (HHI)
	Measures how concentrated transaction sizes are within a wallet. Repeated uniform transfers or a small number of
	dominant-sized transfers can indicate structured behavior.
	
	### Velocity and Movement Patterns
	Evaluates how quickly funds move through the wallet. Higher velocity suggests rapid transmission behavior 
	that can warrant closer review when combined with other signals.
	
	### Burst Activity
	Identifies short-interval clusters of transactions. Sudden activity spikes may indicate attempts to rapidly 
	move funds after receiving flagged assets or during volatile conditions.

	### Surge / Reactivation
	Captures sharp increases in activity relative to recent baseline windows. This can reflect reactivation after
	inactivity or sudden event-driven flows.
	
	### Temporal Spread
	Measures distribution of activity over a 24-hour window. Consistent irregular time patterns may correlate 
	with automation or bot-driven flows.

	### Counterparty Churn
	Measures how quickly a wallet’s counterparties change over time. High churn can indicate peeling chains,
	peeling-like behavior, or rapidly rotating counterparties.
	
	### Sanctions Exposure
	Wallets that interact with addresses linked to sanctions lists receive an amplified priority adjustment.
	The system does not label a wallet as sanctioned; it surfaces exposure signals to guide investigation.
	"""
	)

with st.container(border=True):
	st.subheader("Priority Score Construction")
	st.markdown(
		"""
	Each wallet receives a composite **priority score** between **0 and 100**.

	The priority score is a deterministic, clipped weighted combination of component scores such as:
	- `volume_score`
	- `velocity_score` (with dampening for exchange-like behavior)
	- `burst_score`
	- `time_score`
	- `surge_score`
	- `sanctions_score`
	- `hhi_counterparty_score`
	- `hhi_txn_size_score`
	- `churn_score`

	A conditional interaction bonus can be applied when both size and speed are elevated.

	Sanctions-linked amplification: wallets with non-zero sanctions-linked volume in the rolling window are escalated into a high-priority band so they are reviewed first.
	"""
	)

with st.container(border=True):
	st.subheader("Systemic-Risk Index")
	st.markdown(
		"""
	In addition to wallet-level scoring, StablecoinRiskMonitor computes a macro-level **Systemic-Risk Index** for major USD stablecoins (currently: USDT, USDC, DAI, USDe).

	This index is computed from an hourly aggregated snapshot built from multiple external market-data sources:
	- CoinGecko (CEX price, market cap, volume, exchange price divergence)
	- CoinPaprika (CEX price, market cap, volume)
	- DeFiLlama (supply / issuance metrics)
	- DexPaprika (DEX liquidity + sell/buy pressure metrics)

	The systemic score is a 0–100 composite of component stress indicators:
	- **Peg stress**: deviation of blended price from $1.00.
	- **Liquidity stress**: abnormal changes in DEX depth-to-flow (liquidity relative to 24h DEX volume).
	- **Sell pressure**: abnormal DEX sell/buy imbalance (blended across short + longer windows).
	- **Activity**: abnormal changes in 24h volume.
	- **Supply / issuance shock**: abnormal daily supply change (percent).
	- **Fragmentation**: abnormal exchange-level divergence + cross-source price disagreement.

	A confidence/coverage signal is also computed alongside the systemic score (e.g., how many sources contributed, whether key fields are present). When coverage is low, the systemic score should be interpreted cautiously.
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
	5. **Interpretability:** Surfaces timestamps, components, and coverage signals to support correct use
	"""
	)

with st.container(border=True):
	st.subheader("Disclaimer")
	st.markdown(
		"""
	StablecoinRiskMonitor provides **analytical indicators only**. It does not classify any entity as illicit, 
	sanctioned, or criminal. All outputs support research, transparency, and financial-integrity monitoring.
	
	This content is provided for informational and research purposes only and does not constitute financial, legal, or compliance advice.
	
	Address labeling and entity attribution may be incomplete, outdated, or inaccurate, and should be treated as suggestive context rather than ground truth.
	
	Sanctions-related data (e.g., OFAC SDN-derived address resolution) may also be incomplete, outdated, or inaccurate; absence of a sanctions flag does not imply an address or entity is not sanctioned.
	
	Additional limitations:
	- **Data latency:** Metrics are computed on rolling windows and scheduled snapshots and may not reflect real-time on-chain activity.
	- **Coverage constraints:** Outputs depend on the availability and completeness of upstream data sources and may vary by chain.
	- **False positives/negatives:** Risk indicators are heuristic and may surface benign activity or miss relevant risk.
	- **Sanctions scope:** The sanctions monitor may not include all jurisdictions or lists (e.g., EU/UK/UN) and should not be treated as exhaustive.
	- **No warranty:** Outputs are provided “as is” without warranties; users should independently verify information.
	
	This platform is intended to advance blockchain risk transparency and support compliance investigation, 
	regulatory oversight, and public-interest financial safety.
	"""
	)
