import pandas as pd

def compute_public_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1) volume score (relative)
    max_vol = df["tx_volume_usd"].max()
    if max_vol <= 0:
        df["volume_score"] = 0
    else:
        df["volume_score"] = (df["tx_volume_usd"] / max_vol * 100).clip(0, 100)

    # 2) token profile score
    token_baseline = {
        "USDT": 70,
        "USDC": 50,
    }
    df["token_profile_score"] = df["token"].map(token_baseline).fillna(50)

    # 3) sanctions score
    if "sanctions_flag" in df.columns:
        df["sanctions_score"] = df["sanctions_flag"].astype(int) * 100
    else:
        df["sanctions_score"] = 0

    # 4) final public risk score
    df["risk_score_public"] = (
        0.5 * df["volume_score"]
        + 0.2 * df["token_profile_score"]
        + 0.3 * df["sanctions_score"]
    ).clip(0, 100)


    return df