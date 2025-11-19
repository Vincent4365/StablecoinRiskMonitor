import pandas as pd
import numpy as np
from pathlib import Path

def generate_demo_data(seed=None, n_days=1, n_wallets=10000, save=True):
    """
    Generates a realistic stablecoin dataset and optionally overwrites demo_scores.csv.
    """

    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(None)

    dates = pd.date_range("2025-11-17", periods=n_days, freq="D")
    wallets = [f"Wallet {i}" for i in range(1, n_wallets + 1)]
    tokens = ["USDC", "DAI", "USDe"]

    rows = []

    for wallet in wallets:
        n_tx_wallet = np.random.randint(1, 6)  # 1–5 tx per wallet

        for _ in range(n_tx_wallet):
            date = np.random.choice(dates)
            hour = np.random.randint(1, 25)  # 1–24
            token = np.random.choice(tokens)
            volume = np.random.randint(10, 5_000_000)
            sanction = 1 if np.random.rand() < 0.05 else 0  # 5% sanctions-flagged
            # Store date as string (YYYY-MM-DD), hour as int
            rows.append([pd.Timestamp(date).strftime("%Y-%m-%d"), hour, token, wallet, volume, sanction])

    df = pd.DataFrame(
        rows,
        columns=["date", "hour", "token", "wallet_id", "tx_volume_usd", "sanctions_flag"]
    )

    if save:
        data_path = Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
        df.to_csv(data_path, index=False)
        print(f"[OK] Demo data written to: {data_path}")
        print(f"Rows: {len(df):,} | Wallets: {df['wallet_id'].nunique():,}")

    return df