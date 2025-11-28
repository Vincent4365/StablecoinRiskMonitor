# StablecoinRiskMonitor

Public dashboard and analytics toolkit that monitors stablecoin flows linked to sanctioned addresses and provides transparent AML risk indicators.

## Features

- **Real-time Risk Monitoring**: Track risk scores across major stablecoins (USDT, USDC, DAI, USDe)
- **Sanctions Detection**: Identify wallets with exposure to sanctioned addresses
- **Multi-dimensional Risk Scoring**: Combines transaction volume, velocity, concentration, and temporal patterns
- **Interactive Analytics**: Explore high-risk wallets, volume trends, and risk distributions
- **Privacy-First**: All blockchain addresses are anonymized

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Vincent4365/StablecoinRiskMonitor.git
   cd StablecoinRiskMonitor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the dashboard**
   ```bash
   streamlit run Dashboard.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:8501`

## Data Source

The dashboard operates in **cloud-only mode**, fetching pre-processed stablecoin transaction data from Google Cloud Storage:
- Data is updated every 24 hours
- Includes transactions from major stablecoin protocols
- All wallet addresses are anonymized for privacy
- Sanctions data is cross-referenced with public OFAC lists

## Architecture

### Project Structure
```
StablecoinRiskMonitor/
├── Dashboard.py              # Main dashboard entry point
├── pages/                    # Multi-page Streamlit app
│   ├── 2_Risk_Alerts.py     # High-risk wallet alerts
│   ├── 3_Risk_Scores.py     # Risk score distributions
│   ├── 4_Systemic_Risk_Index.py
│   └── 5_Methodology.py     # Scoring methodology docs
├── utils/                    # Core utilities
│   ├── charts.py            # Plotly chart generation
│   ├── formatting.py        # Data formatting helpers
│   ├── load_data.py         # Cloud data loader (cached)
│   ├── public_scoring.py    # Risk scoring algorithms
│   ├── sidebar.py           # Shared sidebar component
│   └── styling.py           # CSS/icon injection
├── data/
│   ├── sanctions/           # Sanctions reference data
│   └── processed/           # Local cache
└── requirements.txt

```

### Risk Scoring Components

The public risk score (0-100) combines multiple signals:
- **Transaction Volume** (25%): Size and frequency of transfers
- **Token Profile** (20%): Stablecoin type and risk characteristics
- **Wallet Concentration** (20%): Distribution of activity across wallets
- **Velocity/Activity** (20%): Speed of fund movement
- **Burst Score** (10%): Hourly transaction clustering
- **Time Activity** (5%): 24-hour activity spread
- **Sanctions Multiplier**: Applied when wallets interact with sanctioned addresses

### Performance Optimizations
- **Loader-level caching**: Data fetched from cloud is cached for 1 hour
- **Single-pass aggregations**: Wallet-level metrics computed in one groupby operation
- **Pre-binned histograms**: Risk distributions use client-side binning for faster rendering

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and transparency purposes. All blockchain data is publicly available and anonymized.

## Acknowledgments

Built with [Streamlit](https://streamlit.io), [Plotly](https://plotly.com), and [Pandas](https://pandas.pydata.org)
