import pandas as pd

def compute_public_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1) volume score (relative, per transaction)
    max_vol = df["tx_volume_usd"].max()
    if max_vol <= 0:
        df["volume_score"] = 0.0
    else:
        df["volume_score"] = (df["tx_volume_usd"] / max_vol * 100).clip(0, 100)

    # 2) token profile score
    token_baseline = {
        "USDT": 70.0,
        "USDC": 50.0,
    }
    df["token_profile_score"] = df["token"].map(token_baseline).fillna(50.0)

    # 3) sanctions flag (ensure exists and is int)
    if "sanctions_flag" not in df.columns:
        df["sanctions_flag"] = 0
    df["sanctions_flag"] = df["sanctions_flag"].astype(int)

    # wallet-level aggregates
    df["sanctioned_volume"] = df["tx_volume_usd"] * df["sanctions_flag"]

    wallet_agg = (
        df.groupby("wallet_id", as_index=False)
        .agg(
            wallet_total_volume=("tx_volume_usd", "sum"),
            wallet_n_tx=("tx_volume_usd", "count"),
            wallet_sanctions_volume=("sanctioned_volume", "sum"),
        )
    )

    max_wallet_vol = wallet_agg["wallet_total_volume"].max()
    max_wallet_tx = wallet_agg["wallet_n_tx"].max()
    max_wallet_sanctions_vol = wallet_agg["wallet_sanctions_volume"].max()

    # 4) concentration score (wallet share of overall volume)
    if max_wallet_vol <= 0:
        wallet_agg["concentration_score"] = 0.0
    else:
        wallet_agg["concentration_score"] = (
            wallet_agg["wallet_total_volume"] / max_wallet_vol * 100
        ).clip(0, 100)

    # 5) velocity score (wallet activity)
    if max_wallet_tx <= 0:
        wallet_agg["velocity_score"] = 0.0
    else:
        wallet_agg["velocity_score"] = (
            wallet_agg["wallet_n_tx"] / max_wallet_tx * 100
        ).clip(0, 100)

    # 6) sanctions score (wallet-level intensity)
    if max_wallet_sanctions_vol <= 0:
        wallet_agg["sanctions_score"] = (
            (wallet_agg["wallet_sanctions_volume"] > 0).astype(int) * 100.0
        )
    else:
        wallet_agg["sanctions_score"] = (
            wallet_agg["wallet_sanctions_volume"] / max_wallet_sanctions_vol * 100
        ).clip(0, 100)

    # merge wallet-level scores back to each transaction
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

    # 7) final public risk score (v2)
    df["risk_score_public"] = (
        0.25 * df["volume_score"]
        + 0.20 * df["token_profile_score"]
        + 0.20 * df["concentration_score"]
        + 0.20 * df["velocity_score"]
        + 0.15 * df["sanctions_score"]
    ).clip(0, 100)

    df = df.drop(columns=["sanctioned_volume"], errors="ignore")

    return df