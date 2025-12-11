# StablecoinRiskMonitor

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.52.0-red.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109.0-green.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)

Real-time AML risk monitoring platform that identifies high-risk wallet behavior across major stablecoin networks using proprietary risk scoring and interactive visualization.

## Overview

StablecoinRiskMonitor helps analysts, researchers, and compliance teams assess emerging risks in the digital asset ecosystem through blockchain data analysis and advanced risk scoring. The platform processes stablecoin transaction data to identify suspicious patterns and sanctions exposure.

## Key Features

- **Real-time Risk Scoring** across USDT, USDC, DAI, and USDe
- **Sanctions Exposure Detection** linked to OFAC-listed addresses
- **Wallet-Level Behavioral Analysis** (velocity, concentration, burst patterns)
- **Systemic Risk Indicators** revealing emerging market stress patterns
- **Interactive Dashboard** with fast-loading analytics (<5 seconds)
- **Privacy-Preserving Architecture** with anonymized wallet identifiers
- **High-Performance API** serving pre-aggregated data (99.9% data reduction)

## System Architecture

The platform consists of three main components:

### 1. Data Processing Pipeline
- Automated 24-hour batch processing
- Blockchain data extraction and validation
- Proprietary risk scoring engine
- Pre-aggregation for optimal performance
- Secure storage in Google Cloud Storage (Parquet format)

### 2. REST API (FastAPI)
- Deployed on Google Cloud Run (serverless)
- 6 optimized dashboard endpoints
- API key authentication
- 1-hour response caching
- Reduces data transfer from 371K rows to ~300 aggregated rows

### 3. Interactive Dashboard (Streamlit)
- Summary metrics and KPIs
- High-risk wallet rankings (adjustable top 5-100)
- Volume trends and token distribution charts
- Risk score distribution histograms
- Component score breakdowns

## API Endpoints

```
/dashboard/summary              # Key metrics (volume, wallets, avg risk)
/dashboard/top-wallets          # High-risk/whale/sanctions wallets
/dashboard/timeseries           # Volume over time by token
/dashboard/token-volume         # Total volume by stablecoin
/dashboard/risk-distribution    # Risk score histogram
/dashboard/component-scores     # Score breakdown by component
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

The dashboard will connect to the production API automatically. No additional configuration required.

### API Access

The API is hosted at: `https://stablecoin-api-636795230004.us-central1.run.app`

Authentication requires an API key in the `X-API-Key` header. Contact the maintainers for access credentials.

## Technology Stack

- **Frontend**: Streamlit 1.52.0
- **API**: FastAPI 0.109.0 + Uvicorn 0.27.0
- **Data Processing**: Pandas 2.2.0, NumPy 1.26.0
- **Storage**: Google Cloud Storage (Parquet format)
- **Visualization**: Plotly Express
- **Deployment**: Docker + Google Cloud Run

## Performance

- **Load Time**: <5 seconds (vs. previous timeouts)
- **Data Reduction**: 99.9% (371K rows → ~300 aggregated rows)
- **Update Frequency**: Every 24 hours
- **Caching**: 1-hour TTL on API responses

## Author

**Vincent** - [@Vincent4365](https://github.com/Vincent4365)

For questions, feedback, or collaboration opportunities, please open an issue on GitHub.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project advances blockchain risk transparency and supports research, compliance investigation, and public-interest financial safety.
