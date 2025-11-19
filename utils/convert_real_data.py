from pathlib import Path
import pandas as pd

# Ethereum mainnet stablecoin contracts (lowercase)
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
DAI_CONTRACT  = "0x6b175474e89094c44da98b954eedeac495271d0f"
USDE_CONTRACT = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"

# Fixed paths (always used)
RAW_PATH = Path("data/real/raw/raw_bigquery.csv")
OUT_PATH = Path("data/processed/real_scores.csv")


def convert_raw_to_real_scores() -> None:
    """
    Convert raw BigQuery export into anonymized dashboard format.

    Input :  data/real/raw/raw_bigquery.csv
    Output:  data/processed/real_scores.csv

    Output columns:
        date, token, wallet_id, tx_volume_usd, sanctions_flag
    """
    print(f"Reading raw data from: {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)

    # Normalize token address
    df["token_address"] = df["token_address"].str.lower()

    # Map contract -> token symbol
    token_map = {
        USDC_CONTRACT: "USDC",
        DAI_CONTRACT:  "DAI",
        USDE_CONTRACT: "USDe",
    }
    df["token"] = df["token_address"].map(token_map).fillna("UNKNOWN")

    df["tx_volume_usd"] = df["token_amount"].astype(float)

    # Wallet anonymization
    df["wallet_raw"] = df["from_address"].str.lower()
    codes, uniques = pd.factorize(df["wallet_raw"])
    df["wallet_id"] = [f"Wallet {i+1}" for i in codes]

    # Extract date (yyyy-mm-dd only)
    df["date"] = pd.to_datetime(df["block_timestamp"]).dt.date
    df["date"] = pd.to_datetime(df["date"])

    # Placeholder sanctions flag (always 0)
    df["sanctions_flag"] = 0

    # Final cleaned output
    out = df[["date", "token", "wallet_id", "tx_volume_usd", "sanctions_flag"]]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print(f"Wrote anonymized dataset to: {OUT_PATH.resolve()}")
    print(f"Rows: {len(out):,}")
    print(out.head())


if __name__ == "__main__":
    convert_raw_to_real_scores()