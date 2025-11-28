import pandas as pd
import numpy as np
import streamlit as st

def compute_public_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute risk scores for transactions.
    
    Note: Caching is handled at the data loader level (load_cloud_data),
    so this function does not need its own cache decorator.
    """
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
    wallet_agg["burst_score"] = _burst_score(wallet_agg)
    wallet_agg["time_score"] = _time_activity_score(wallet_agg)

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
    """Calculate volume-based risk score (0-100) using log scaling.
    
    Higher transaction volumes receive higher scores. Uses logarithmic scaling
    to normalize across wide ranges of transaction sizes.
    """
    vol = df["tx_volume_usd"].clip(lower=1)
    log_vol = np.log10(vol)
    max_log = log_vol.max()
    if max_log <= 0:
        return pd.Series([0.0] * len(df))
    return (log_vol / max_log * 100).clip(0, 100)


def _token_profile_score(df: pd.DataFrame) -> pd.Series:
    """Assign baseline risk scores by token type.
    
    Different stablecoins have different risk profiles based on their
    characteristics, usage patterns, and regulatory exposure.
    """
    token_baseline = {
        "USDT": 70.0,
        "USDC": 50.0,
        "DAI": 55.0,
        "USDe": 60.0,
    }
    return df["token"].map(token_baseline).fillna(50.0)


def _ensure_sanctions_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure sanctions_flag column exists and is properly typed.
    
    Creates the column with default value 0 if missing, ensuring
    subsequent scoring logic can safely reference it.
    """
    if "sanctions_flag" not in df.columns:
        df["sanctions_flag"] = 0
    df["sanctions_flag"] = df["sanctions_flag"].astype(int)
    return df


def _wallet_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all wallet-level aggregations in a single pass for performance.
    
    Consolidates multiple groupby operations into one to reduce processing time.
    Calculates total volume, transaction count, sanctions exposure, burst activity,
    and temporal spread for each wallet.
    """
    df["sanctioned_volume"] = df["tx_volume_usd"] * df["sanctions_flag"]

    # Consolidate all wallet-level aggregations in a single groupby for performance
    agg_dict = {
        "wallet_total_volume": ("tx_volume_usd", "sum"),
        "wallet_n_tx": ("tx_volume_usd", "count"),
        "wallet_sanctions_volume": ("sanctioned_volume", "sum"),
        "wallet_burst": ("hour", lambda x: x.value_counts().max() if len(x) > 0 else 0),
        "active_hours": ("hour", "nunique"),
    }
    
    return df.groupby("wallet_id", as_index=False).agg(**agg_dict)


def _concentration_score(wallet_agg: pd.DataFrame) -> pd.Series:
    """Calculate concentration score based on wallet total volume.
    
    Wallets handling larger volumes receive higher scores, indicating
    potential systemic risk or whale activity.
    """
    max_vol = wallet_agg["wallet_total_volume"].max()
    if max_vol <= 0:
        return pd.Series([0.0] * len(wallet_agg))
    return (wallet_agg["wallet_total_volume"] / max_vol * 100).clip(0, 100)


def _velocity_score(wallet_agg: pd.DataFrame) -> pd.Series:
    """Calculate velocity score based on transaction count.
    
    Higher transaction frequency suggests automated trading, mixing services,
    or high-activity operations.
    """
    max_tx = wallet_agg["wallet_n_tx"].max()
    if max_tx <= 0:
        return pd.Series([0.0] * len(wallet_agg))
    return (wallet_agg["wallet_n_tx"] / max_tx * 100).clip(0, 100)


def _sanctions_score(wallet_agg: pd.DataFrame) -> pd.Series:
    """Calculate sanctions exposure score based on sanctioned volume.
    
    Wallets with any sanctions exposure receive maximum score. If multiple
    wallets have sanctions exposure, scores are scaled by relative volume.
    """
    max_sanctions_vol = wallet_agg["wallet_sanctions_volume"].max()
    if max_sanctions_vol <= 0:
        # binary: any sanctions = 100
        return (wallet_agg["wallet_sanctions_volume"] > 0).astype(int) * 100.0
    return (
        wallet_agg["wallet_sanctions_volume"] / max_sanctions_vol * 100
    ).clip(0, 100)

def _burst_score(wallet_agg: pd.DataFrame) -> pd.Series:
    """
    Measures how many transactions each wallet performs in its busiest hour.
    High = bursty behavior (common in mixers, layering, consolidation bots).
    
    Uses pre-computed wallet_burst from aggregates for performance.
    """
    max_burst = wallet_agg["wallet_burst"].max()
    if max_burst <= 0:
        return pd.Series([0.0] * len(wallet_agg))

    return (wallet_agg["wallet_burst"] / max_burst * 100).clip(0, 100)


def _time_activity_score(wallet_agg: pd.DataFrame) -> pd.Series:
    """
    Measures how many distinct hours a wallet is active in.
    High = bot-like or systematic behavior.
    Low = predictable human trading clusters.
    
    Uses pre-computed active_hours from aggregates for performance.
    """
    return (wallet_agg["active_hours"] / 24 * 100).clip(0, 100)


