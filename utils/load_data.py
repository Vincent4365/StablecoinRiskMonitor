import pandas as pd
from pathlib import Path

def load_demo_data():
    data_path = Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
    df = pd.read_csv(data_path, parse_dates=["date"])
    return df