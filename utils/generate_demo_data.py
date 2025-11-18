import pandas as pd
import numpy as np
from pathlib import Path

def generate_demo_data(n_days=50, n_wallets=60, save=True):
    """
    Generates a realistic stablecoin dataset and optionally overwrites demo_scores.csv.
    """

    np.random.seed(None)

    dates = pd.date_range("2025-10-01", periods=n_days, freq="D")
    wallets = [f"Wallet {i}" for i in range(1, n_wallets + 1)]
    tokens = ["USDT", "USDC"]

    rows = []

    for date in dates:
        n_tx = np.random.randint(4, 16)  # 4–7 tx per day
        for _ in range(n_tx):
            wallet = np.random.choice(wallets)
            token = np.random.choice(tokens)
            volume = np.random.randint(10000, 900000)
            sanction = 1 if np.random.rand() < 0.05 else 0  # 5% sanctions-flagged
            rows.append([date, token, wallet, volume, sanction])

    df = pd.DataFrame(
        rows,
        columns=["date", "token", "wallet_id", "tx_volume_usd", "sanctions_flag"]
    )

    # Overwrite demo_scores.csv if save=True
    if save:
        data_path = (
            Path(__file__).parent.parent / "data" / "sample" / "demo_scores.csv"
        )
        df.to_csv(data_path, index=False)
        print(f"[OK] Demo data written to: {data_path}")

    return df