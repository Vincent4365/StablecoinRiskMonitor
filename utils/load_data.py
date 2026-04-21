"""Legacy API loader (minimized).

This module remains only for pages that still import a small set of functions.
All other legacy dashboard helpers were removed as part of repo cleanup.

Kept functions:
- `get_top_counterparties`
- `get_eth_rich_list`
- `get_tron_rich_list`
"""

from __future__ import annotations

import logging

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)


def get_top_counterparties(top_n: int = 100, hours: int = 24, chain: str = "eth") -> pd.DataFrame:
    try:
        return _cached_get_top_counterparties(top_n=top_n, hours=hours, chain=chain)
    except _ApiConfigError as e:
        st.error(str(e))
        return pd.DataFrame()
    except Exception as e:
        logger.exception("Error fetching top counterparties: %s", e)
        st.error(f"Failed to fetch top counterparties: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_get_top_counterparties(top_n: int = 100, hours: int = 24, chain: str = "eth") -> pd.DataFrame:
    api_url, api_key = _require_api_config()

    # Only the 24h window is supported for this dataset.
    if hours != 24:
        hours = 24

    headers = {"X-API-Key": api_key}
    params = {
        "top_n": top_n,
        "hours": hours,
        "include_labels": "true",
        "chain": chain,
    }
    resp = requests.get(f"{api_url}/dashboard/top-counterparties", headers=headers, params=params, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    return pd.DataFrame(data.get("data", []))


class _ApiConfigError(RuntimeError):
    pass


def _require_api_config() -> tuple[str, str]:
    api_url = st.secrets.get("API_URL", "https://stablecoin-api-636795230004.us-central1.run.app")
    api_key = st.secrets.get("API_KEY")
    if not api_key:
        raise _ApiConfigError("API_KEY not found in secrets. Please configure .streamlit/secrets.toml")
    return str(api_url).rstrip("/"), str(api_key)


def get_eth_rich_list(token_address: str, limit: int = 100) -> pd.DataFrame:
    """Fetch Ethereum rich list from the API (Parquet-backed).

    `limit` is capped to 1000 to match the exported Parquet snapshots.
    """
    try:
        return _cached_get_eth_rich_list(token_address=token_address, limit=limit)
    except _ApiConfigError as e:
        st.error(str(e))
        return pd.DataFrame()
    except Exception as e:
        logger.exception("Error fetching ETH rich list: %s", e)
        st.error(f"Failed to fetch rich list: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_get_eth_rich_list(token_address: str, limit: int = 100) -> pd.DataFrame:
    api_url, api_key = _require_api_config()

    token = (token_address or "").strip().lower()
    if not token:
        return pd.DataFrame()

    try:
        capped_limit = int(limit)
    except Exception:
        capped_limit = 100
    capped_limit = max(1, min(1000, capped_limit))

    headers = {"X-API-Key": api_key}
    params = {"token": token, "limit": capped_limit}
    resp = requests.get(f"{api_url}/data/rich-list", headers=headers, params=params, timeout=30)
    resp.raise_for_status()

    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        return pd.DataFrame()

    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)
    if "token_address" not in df.columns:
        df["token_address"] = token

    df["chain"] = "Ethereum"
    return df


def get_tron_rich_list(limit: int = 100) -> pd.DataFrame:
    """Fetch TRON USDT rich list from the API (Parquet-backed).

    `limit` is capped to 1000 to match the exported Parquet snapshots.
    """
    try:
        return _cached_get_tron_rich_list(limit=limit)
    except _ApiConfigError as e:
        st.error(str(e))
        return pd.DataFrame()
    except Exception as e:
        logger.exception("Error fetching TRON rich list: %s", e)
        st.error(f"Failed to fetch TRON rich list: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_get_tron_rich_list(limit: int = 100) -> pd.DataFrame:
    api_url, api_key = _require_api_config()

    try:
        capped_limit = int(limit)
    except Exception:
        capped_limit = 100
    capped_limit = max(1, min(1000, capped_limit))

    headers = {"X-API-Key": api_key}
    params = {"limit": capped_limit}
    resp = requests.get(f"{api_url}/data/rich-list/tron", headers=headers, params=params, timeout=30)
    resp.raise_for_status()

    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        return pd.DataFrame()

    if "balance" in df.columns:
        df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)

    df["chain"] = "Tron"
    return df



@st.cache_data(ttl=3600)
def get_tron_timeseries_data(hours: int = 24) -> pd.DataFrame:
    df = get_tron_scores()
    if df.empty:
        return pd.DataFrame()

    df = _filter_tron_by_hours(df, hours)
    if df.empty:
        return pd.DataFrame()

    volume_col = "tx_volume_usd" if "tx_volume_usd" in df.columns else "usdt_amount"
    dt = pd.to_datetime(df.get("datetime"), errors="coerce", utc=True)
    df = df.copy()
    df["datetime"] = dt.dt.floor("h").dt.tz_convert(None)
    df["Token"] = df.get("token", "USDT")
    df["Volume"] = pd.to_numeric(df.get(volume_col, 0.0), errors="coerce").fillna(0.0)

    out = (
        df.groupby(["datetime", "Token"], as_index=False)["Volume"]
        .sum()
        .sort_values(["datetime", "Token"], ascending=[True, True])
    )
    return out


@st.cache_data(ttl=3600)
def get_tron_token_volume(hours: int = 24) -> pd.DataFrame:
    ts = get_tron_timeseries_data(hours=hours)
    if ts.empty:
        return pd.DataFrame()
    return ts.groupby("Token", as_index=False)["Volume"].sum()


@st.cache_data(ttl=3600)
def get_tron_risk_distribution(tokens: list = None, hours: int = 24) -> pd.DataFrame:
    df = get_tron_scores()
    if df.empty or "risk_score" not in df.columns:
        return pd.DataFrame()

    df = _filter_tron_by_hours(df, hours)
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["Token"] = df.get("token", "USDT")
    if tokens:
        df = df[df["Token"].isin(tokens)]
        if df.empty:
            return pd.DataFrame()

    risk = pd.to_numeric(df["risk_score"], errors="coerce").dropna()
    if risk.empty:
        return pd.DataFrame()

    edges = np.linspace(0.0, 100.0, 26)
    df["_bin"] = pd.cut(pd.to_numeric(df["risk_score"], errors="coerce"), bins=edges, include_lowest=True, right=False)
    counts = df.groupby(["Token", "_bin"], as_index=False).size().rename(columns={"size": "count"})

    # Expand bin intervals into start/end floats
    counts["bin_start"] = pd.to_numeric(counts["_bin"].apply(lambda b: float(b.left) if pd.notna(b) else None), errors="coerce")
    counts["bin_end"] = pd.to_numeric(counts["_bin"].apply(lambda b: float(b.right) if pd.notna(b) else None), errors="coerce")
    counts = counts.drop(columns=["_bin"])

    return counts[["Token", "count", "bin_start", "bin_end"]]


@st.cache_data(ttl=3600)
def get_tron_component_scores(tokens: list = None, hours: int = 24) -> pd.DataFrame:
    df = get_tron_scores()
    if df.empty:
        return pd.DataFrame()

    df = _filter_tron_by_hours(df, hours)
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["Token"] = df.get("token", "USDT")
    if tokens:
        df = df[df["Token"].isin(tokens)]
        if df.empty:
            return pd.DataFrame()

    def _mean(col: str) -> float:
        if col not in df.columns:
            return 0.0
        return float(pd.to_numeric(df[col], errors="coerce").mean())

    grouped = df.groupby("Token", as_index=False).agg(
        **{
            "Volume Score": ("volume_score", "mean"),
            "Token Profile": ("token_profile_score", "mean"),
            "Concentration": ("concentration_score", "mean"),
            "Velocity": ("velocity_score", "mean"),
            "Burst": ("burst_score", "mean"),
            "Time Score": ("time_score", "mean"),
            "Overall Risk": ("risk_score", "mean"),
        }
    )

    # TRON export currently has no sanctions intensity component; keep schema consistent.
    grouped["Sanctions"] = 0.0
    cols = [
        "Token",
        "Volume Score",
        "Token Profile",
        "Concentration",
        "Velocity",
        "Sanctions",
        "Burst",
        "Time Score",
        "Overall Risk",
    ]
    return grouped[cols]


def _is_tron(chain: str) -> bool:
    return str(chain).strip().lower() in {"tron", "trx"}


@st.cache_data(ttl=3600)
def get_dashboard_summary_chain(chain: str, hours: int = 24) -> dict:
    if _is_tron(chain):
        return get_tron_dashboard_summary(hours=hours)
    return get_dashboard_summary(hours=hours)


@st.cache_data(ttl=3600)
def get_top_wallets_chain(chain: str, top_n: int = 100, sort_by: str = "risk", hours: int = 24) -> pd.DataFrame:
    if _is_tron(chain):
        return get_tron_top_wallets(top_n=top_n, sort_by=sort_by, hours=hours)
    return get_top_wallets(top_n=top_n, sort_by=sort_by, hours=hours)


@st.cache_data(ttl=3600)
def get_timeseries_data_chain(chain: str, hours: int = 24) -> pd.DataFrame:
    if _is_tron(chain):
        return get_tron_timeseries_data(hours=hours)
    return get_timeseries_data(hours=hours)


@st.cache_data(ttl=3600)
def get_token_volume_chain(chain: str, hours: int = 24) -> pd.DataFrame:
    if _is_tron(chain):
        return get_tron_token_volume(hours=hours)
    return get_token_volume(hours=hours)


@st.cache_data(ttl=3600)
def get_risk_distribution_chain(chain: str, tokens: list = None, hours: int = 24) -> pd.DataFrame:
    if _is_tron(chain):
        return get_tron_risk_distribution(tokens=tokens, hours=hours)
    return get_risk_distribution(tokens=tokens)


@st.cache_data(ttl=3600)
def get_component_scores_chain(chain: str, tokens: list = None, hours: int = 24) -> pd.DataFrame:
    if _is_tron(chain):
        return get_tron_component_scores(tokens=tokens, hours=hours)
    return get_component_scores(tokens=tokens)
