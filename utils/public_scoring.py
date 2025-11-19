import pandas as pd

def _volume_score(df: pd.DataFrame) -> pd.Series:
    max_vol = df["tx_volume_usd"].max()
    if max_vol <= 0:
        return pd.Series([0.0] * len(df))
    return (df["tx_volume_usd"] / max_vol * 100).clip(0, 100)


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


def compute_public_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1) volume score
    df["volume_score"] = _volume_score(df)

    # 2) token profile score
    df["token_profile_score"] = _token_profile_score(df)

    # 3) sanctions flag normalization
    df = _ensure_sanctions_flag(df)

    # 4) wallet-level aggregation
    wallet_agg = _wallet_aggregates(df)

    # 5) wallet-level scores
    wallet_agg["concentration_score"] = _concentration_score(wallet_agg)
    wallet_agg["velocity_score"] = _velocity_score(wallet_agg)
    wallet_agg["sanctions_score"] = _sanctions_score(wallet_agg)

    # merge back to each transaction
    df = df.merge(
        wallet_agg[
            [
                "wallet_id",
                "concentration_score",
                "velocity_score",
                "sanctions_score",
            ]
        ],
        on="wallet_id",
        how="left",
    )

    # 6) final public risk score
    df["risk_score_public"] = (
        0.25 * df["volume_score"]
        + 0.20 * df["token_profile_score"]
        + 0.20 * df["concentration_score"]
        + 0.20 * df["velocity_score"]
        + 0.15 * df["sanctions_score"]
    ).clip(0, 100)

    # cleanup
    df = df.drop(columns=["sanctioned_volume"], errors="ignore")

    return df