# System Architecture

## Overview

StablecoinRiskMonitor is a real-time AML risk monitoring platform that identifies high-risk wallet behavior across major stablecoin networks using proprietary risk scoring and interactive visualization.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│              Blockchain Data Sources                    │
│  • Ethereum, BSC, Polygon Networks                      │
│  • USDT, USDC, DAI, USDe Transactions                  │
│  • OFAC Sanctions Lists                                 │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│           Processing Pipeline (24h cycle)               │
│  • Transaction extraction & anonymization              │
│  • Proprietary risk scoring engine                     │
│  • Wallet aggregation & analytics                      │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│         Cloud Storage (Google Cloud Storage)            │
│  • Processed data (Parquet format)                     │
│  • Pre-aggregated analytics                            │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│            REST API (FastAPI + Cloud Run)               │
│  • 6 optimized dashboard endpoints                     │
│  • API key authentication                              │
│  • 99.9% data reduction (371K → 300 rows)             │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│          Interactive Dashboard (Streamlit)              │
│  • Risk metrics & alerts                               │
│  • Wallet analysis & rankings                          │
│  • Volume trends & distributions                       │
│  • Load time: <5 seconds                               │
└────────────────────────────────────────────────────────┘
```

## Key Features

- **Performance**: 99.9% data reduction through pre-aggregation (371K → 300 rows)
- **Speed**: Dashboard loads in <5 seconds with 1-hour caching
- **Security**: API key authentication with private cloud storage
- **Privacy**: All wallet addresses anonymized
- **Scalability**: Serverless Cloud Run auto-scaling

## Technology Stack

- **Frontend**: Streamlit (interactive dashboards)
- **API**: FastAPI + Cloud Run (serverless REST API)
- **Data**: Pandas + NumPy (analytics engine)
- **Storage**: Google Cloud Storage (Parquet format)
- **Visualization**: Plotly (interactive charts)
- **Deployment**: Docker + Cloud Build
