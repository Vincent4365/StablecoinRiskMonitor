import pandas as pd
from pathlib import Path
from utils.public_scoring import compute_public_risk_scores
import streamlit as st

@st.cache_data
def load_demo_data():
    data_path = Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
    df = pd.read_csv(data_path)
    df = compute_public_risk_scores(df)
    return df

@st.cache_data
def load_real_data() -> pd.DataFrame:
    """Load anonymized real-world stablecoin data."""
    path = Path(__file__).parent.parent / "data" / "processed" / "real_scores.csv"
    df = pd.read_csv(path)

    df = compute_public_risk_scores(df)
    return df

@st.cache_data
def load_sanctions_list() -> pd.DataFrame:
    sanctions_path = Path(st.secrets["sanctions"]["file_path"])

    if not sanctions_path.exists():
        st.warning("Sanctions list not found.")
        return pd.DataFrame(columns=["address"])

    df = pd.read_csv(sanctions_path)
    df["address"] = df["address"].str.lower()
    return df