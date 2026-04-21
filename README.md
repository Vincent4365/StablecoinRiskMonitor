# StablecoinRiskMonitor

![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-dashboard-red.svg)
![FastAPI](https://img.shields.io/badge/fastapi-api-green.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)

AML risk monitoring platform that identifies high-risk wallet behavior across major stablecoin networks using risk scoring and interactive visualization.

## Overview

StablecoinRiskMonitor helps analysts, researchers, and compliance teams assess emerging risks in the digital asset ecosystem through blockchain data analysis and advanced risk scoring. The platform processes stablecoin transaction data to identify suspicious patterns and sanctions exposure.

## Key Features

- **Risk Scoring** across major stablecoins
- **Sanctions Exposure Detection** linked to OFAC-listed addresses
- **Wallet-Level Behavioral Analysis** (velocity, concentration, burst patterns)
- **Systemic Risk Indicators** revealing emerging market stress patterns
- **Interactive Dashboard** for exploration and monitoring
- **API-backed Architecture** serving pre-aggregated data

## System Architecture

The platform consists of three main components:

### 1. Data Processing Pipeline
- Scheduled data exports and aggregation
- Pre-aggregation for dashboard performance
- Storage in Google Cloud Storage (Parquet)

### 2. REST API (FastAPI)
- Deployed on Google Cloud Run (serverless)
- API key authentication
- Endpoint-level caching (where appropriate)

### 3. Interactive Dashboard (Streamlit)
- Summary metrics and KPIs
- High-risk wallet rankings (adjustable top 5-100)
- Volume trends and token distribution charts
- Risk score distribution histograms
- Component score breakdowns

## API Endpoints

```
/dashboard/total-wallets-tracked     # KPI snapshot (chain=eth|tron)
/dashboard/top-counterparties        # Top counterparties (24h, chain=eth|tron)
/dashboard/timeseries-snapshot       # Volume timeseries (24h, chain=eth|tron)
/dashboard/token-volume-snapshot     # Token volume totals (24h, chain=eth|tron)
/wallet-metrics/*                   # Rolling/hourly wallet metrics + whale alerts
/ae/*                               # A–E stablecoin aggregate exports
```

## Risk Scoring Methodology

Risk scores (0-100) are calculated using a proprietary weighted aggregation of multiple indicators:

- **Transaction Volume**: Log-scaled systemic importance
- **Token Risk Profile**: Stablecoin-specific risk characteristics
- **Concentration Metrics**: Transaction size distribution (Herfindahl index)
- **Behavioral Patterns**: Velocity, burst activity, temporal spread
- **Sanctions Exposure**: Amplification for OFAC-listed interactions

Specific weights and formulas are proprietary to maintain scoring integrity, but the methodology follows established AML risk assessment frameworks. See the Methodology page in the dashboard for more details.

## Impact

StablecoinRiskMonitor contributes to:

- Enhanced AML monitoring
- Early-risk detection for regulators, exchanges, and financial institutions
- Greater transparency in a sector processing billions in daily volume
- Improved systemic-risk visibility for researchers and policymakers

This project supports the broader goal of strengthening the safety and integrity of U.S. financial systems as digital-assets usage continues to expand.

## Installation & Usage

### Running the Dashboard Locally

```bash
git clone https://github.com/Vincent4365/StablecoinRiskMonitor.git
cd StablecoinRiskMonitor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run Dashboard.py
```

The dashboard connects to an API. For local runs, configure `API_URL` and `API_KEY` via Streamlit secrets (see `.streamlit/secrets.toml`).

### API Access

The API is hosted at: `https://stablecoin-api-636795230004.us-central1.run.app`

Authentication requires an API key in the `X-API-Key` header.

## Technology Stack

- **Frontend**: Streamlit
- **API**: FastAPI
- **Data Processing**: Pandas, NumPy
- **Storage**: Google Cloud Storage (Parquet format)
- **Visualization**: Plotly Express
- **Deployment**: Docker + Google Cloud Run

## Author

**Vincent** - [@Vincent4365](https://github.com/Vincent4365)

For questions, feedback, or collaboration opportunities, please open an issue on GitHub.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project advances blockchain risk transparency and supports research, compliance investigation, and public-interest financial safety.
