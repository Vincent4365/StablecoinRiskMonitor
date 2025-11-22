import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def compute_public_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute risk scores with caching to improve performance."""
    return _compute_risk_scores_internal(df)

def _compute_risk_scores_internal(df: pd.DataFrame) -> pd.DataFrame:
    """Internal scoring function called by cached wrapper."""
    df = df.copy()

    # volume score
    df["volume_score"] = _volume_score(df)

    # token profile score
    df["token_profile_score"] = _token_profile_score(df)

    # sanctions flag normalization
    df = _ensure_sanctions_flag(df)

    # wallet-level aggregation
    wallet_agg = _wallet_aggregates(df)

    # wallet-level scores
    wallet_agg["concentration_score"] = _concentration_score(wallet_agg)
    wallet_agg["velocity_score"] = _velocity_score(wallet_agg)
    wallet_agg["sanctions_score"] = _sanctions_score(wallet_agg)
    wallet_agg["burst_score"] = _burst_score(df, wallet_agg)
    wallet_agg["time_score"] = _time_activity_score(df, wallet_agg)

    # merge back to each transaction
    df = df.merge(
        wallet_agg[
            [
                "wallet_id",
                "concentration_score",
                "velocity_score",
                "sanctions_score",
                "burst_score",
                "time_score",
            ]
        ],
        on="wallet_id",
        how="left",
    )

    base_score = (
        0.25 * df["volume_score"]
        + 0.20 * df["token_profile_score"]
        + 0.20 * df["concentration_score"]
        + 0.20 * df["velocity_score"]
        + 0.10 * df["burst_score"]
        + 0.05 * df["time_score"]
)

    df["risk_score_public"] = base_score

    sanctions_multiplier = np.where(
        df["sanctions_flag"] == 1,
        1 + np.log10(df["tx_volume_usd"].clip(lower=1)) / 2,
        1.0
    )
    
    df["risk_score_public"] = df["risk_score_public"] * sanctions_multiplier
    df["risk_score_public"] = df["risk_score_public"].clip(0, 100)

    # cleanup
    df = df.drop(columns=["sanctioned_volume"], errors="ignore")

    # rename columns
    rename_map = {
    "date": "Date",
    "hour": "Hour",
    "token": "Token",
    "wallet_id": "Wallet",
    "tx_volume_usd": "Volume",
    "sanctions_flag": "Sanctioned",

    "volume_score": "Volume Score",
    "token_profile_score": "Token Score",
    "concentration_score": "Concentration Score",
    "velocity_score": "Velocity Score",
    "sanctions_score": "Sanctions Score",
    "burst_score": "Burst Score",
    "time_score": "Time Score",

    "risk_score_public": "Risk Score",
}

    df = df.rename(columns=rename_map)

    return df

def _volume_score(df: pd.DataFrame) -> pd.Series:
    vol = df["tx_volume_usd"].clip(lower=1)
    log_vol = np.log10(vol)
    max_log = log_vol.max()
    if max_log <= 0:
        return pd.Series([0.0] * len(df))
    return (log_vol / max_log * 100).clip(0, 100)


def _token_profile_score(df: pd.DataFrame) -> pd.Series:
    token_baseline = {
        "USDT": 70.0,
        "USDC": 50.0,
        "DAI": 55.0,
        "USDe": 60.0,
    }
    return df["token"].map(token_baseline).fillna(50.0)


def _ensure_sanctions_flag(df: pd.DataFrame) -> pd.DataFrame:
    if "sanctions_flag" not in df.columns:
        df["sanctions_flag"] = 0
    df["sanctions_flag"] = df["sanctions_flag"].astype(int)
    return df


def _wallet_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    df["sanctioned_volume"] = df["tx_volume_usd"] * df["sanctions_flag"]

    return (
        df.groupby("wallet_id", as_index=False)
        .agg(
            wallet_total_volume=("tx_volume_usd", "sum"),
            wallet_n_tx=("tx_volume_usd", "count"),
            wallet_sanctions_volume=("sanctioned_volume", "sum"),
        )
    )


def _concentration_score(wallet_agg: pd.DataFrame) -> pd.Series:
    max_vol = wallet_agg["wallet_total_volume"].max()
    if max_vol <= 0:
        return pd.Series([0.0] * len(wallet_agg))
    return (wallet_agg["wallet_total_volume"] / max_vol * 100).clip(0, 100)


def _velocity_score(wallet_agg: pd.DataFrame) -> pd.Series:
    max_tx = wallet_agg["wallet_n_tx"].max()
    if max_tx <= 0:
        return pd.Series([0.0] * len(wallet_agg))
    return (wallet_agg["wallet_n_tx"] / max_tx * 100).clip(0, 100)


def _sanctions_score(wallet_agg: pd.DataFrame) -> pd.Series:
    max_sanctions_vol = wallet_agg["wallet_sanctions_volume"].max()
    if max_sanctions_vol <= 0:
        # binary: any sanctions = 100
        return (wallet_agg["wallet_sanctions_volume"] > 0).astype(int) * 100.0
    return (
        wallet_agg["wallet_sanctions_volume"] / max_sanctions_vol * 100
    ).clip(0, 100)

def _burst_score(df: pd.DataFrame, wallet_agg: pd.DataFrame) -> pd.Series:
    """
    Measures how many transactions each wallet performs in its busiest hour.
    High = bursty behavior (common in mixers, layering, consolidation bots).
    """
    hourly = (
        df.groupby(["wallet_id", "hour"])
        .size()
        .reset_index(name="tx_count")
    )

    burst = (
        hourly.groupby("wallet_id")["tx_count"]
        .max()
        .reset_index(name="wallet_burst")
    )

    merged = wallet_agg[["wallet_id"]].merge(burst, on="wallet_id", how="left")
    merged["wallet_burst"] = merged["wallet_burst"].fillna(0)

    max_burst = merged["wallet_burst"].max()
    if max_burst <= 0:
        return pd.Series([0.0] * len(wallet_agg))

    return (merged["wallet_burst"] / max_burst * 100).clip(0, 100)


def _time_activity_score(df: pd.DataFrame, wallet_agg: pd.DataFrame) -> pd.Series:
    """
    Measures how many distinct hours a wallet is active in.
    High = bot-like or systematic behavior.
    Low = predictable human trading clusters.
    """
    hours_active = (
        df.groupby("wallet_id")["hour"]
        .nunique()
        .reset_index(name="active_hours")
    )

    merged = wallet_agg[["wallet_id"]].merge(hours_active, on="wallet_id", how="left")
    merged["active_hours"] = merged["active_hours"].fillna(0)

    return (merged["active_hours"] / 24 * 100).clip(0, 100)


