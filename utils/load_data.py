import pandas as pd
from pathlib import Path
from utils.public_scoring import compute_public_risk_scores

def load_demo_data():
    data_path = Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
    df = pd.read_csv(data_path, parse_dates=["date"])
    df = compute_public_risk_scores(df)
    return df