import pandas as pd
from pathlib import Path
from utils.public_scoring import compute_public_risk_scores

def load_demo_data():
    data_path = Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
    df = pd.read_csv(data_path, parse_dates=["date"])
    df = compute_public_risk_scores(df)
    return df

def load_real_data() -> pd.DataFrame:
    """
    Load anonymized real-world stablecoin data exported from BigQuery.

    Expects a CSV created by the anonymizer:
        data/real/real_scores.csv
    with columns: date, token, wallet_id, tx_volume_usd, sanctions_flag
    """
    path = Path(__file__).parent.parent / "data" / "processed" / "real_scores.csv"
    df = pd.read_csv(path, parse_dates=["date"])

    df = compute_public_risk_scores(df)
    return df