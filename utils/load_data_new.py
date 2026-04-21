import logging
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class _ApiConfigError(RuntimeError):
    pass


def _require_api_config() -> tuple[str, str]:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        raise _ApiConfigError("API_URL/API_KEY missing")
    return str(api_url), str(api_key)


def _get_api_config():
    api_url = st.secrets.get("API_URL", "https://stablecoin-api-636795230004.us-central1.run.app")
    api_key = st.secrets.get("API_KEY")

    if not api_key:
        st.error("API_KEY not found in secrets. Please configure .streamlit/secrets.toml")
        return None, None

    return api_url, api_key


def _chain_to_param(chain: str) -> str:
    c = str(chain or "").strip().lower()
    if c in {"tron", "trx"}:
        return "tron"
    return "eth"


def get_whale_alert_tokens(*, limit: int = 1000) -> tuple[list[str], str | None]:
    """Return (tokens, last_modified) from `/wallet-metrics/whale-alerts/tokens`."""
    try:
        return _cached_get_whale_alert_tokens(limit=limit)
    except _ApiConfigError:
        return [], None
    except Exception as e:
        logger.exception("Error fetching whale alert tokens: %s", e)
        st.error(f"Failed to fetch whale alert tokens: {e}")
        return [], None


@st.cache_data(ttl=3600)
def _cached_get_whale_alert_tokens(*, limit: int = 1000) -> tuple[list[str], str | None]:
    api_url, api_key = _require_api_config()

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/wallet-metrics/whale-alerts/tokens",
        headers=headers,
        params={"limit": int(limit)},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    data = payload.get("data") if isinstance(payload, dict) else None
    tokens = [str(x) for x in data if x] if isinstance(data, list) else []
    last_modified = payload.get("last_modified") if isinstance(payload, dict) else None
    return tokens, last_modified


def get_whale_alerts(
    *,
    chain: str | None = None,
    token_symbol: str | None = None,
    min_amount_usd: float | None = None,
    event_type: str | None = None,
    days: int = 30,
    limit: int = 500,
) -> tuple[pd.DataFrame, str | None]:
    """Return (df, last_modified) from `/wallet-metrics/whale-alerts`.

    This is Parquet-backed on the API side; this client still talks to the API
    and (when enabled) requires an API key.
    """
    try:
        return _cached_get_whale_alerts(
            chain=chain,
            token_symbol=token_symbol,
            min_amount_usd=min_amount_usd,
            event_type=event_type,
            days=days,
            limit=limit,
        )
    except _ApiConfigError:
        return pd.DataFrame(), None
    except Exception as e:
        logger.exception("Error fetching whale alerts: %s", e)
        st.error(f"Failed to fetch whale alerts: {e}")
        return pd.DataFrame(), None


@st.cache_data(ttl=300)
def _cached_get_whale_alerts(
    *,
    chain: str | None = None,
    token_symbol: str | None = None,
    min_amount_usd: float | None = None,
    event_type: str | None = None,
    days: int = 30,
    limit: int = 500,
) -> tuple[pd.DataFrame, str | None]:
    api_url, api_key = _require_api_config()

    params: dict[str, object] = {"limit": int(limit), "days": int(days)}
    if chain:
        params["chain"] = str(chain).strip().lower()
    if token_symbol:
        params["token_symbol"] = str(token_symbol).strip()
    if min_amount_usd is not None and float(min_amount_usd) > 0:
        params["min_amount_usd"] = float(min_amount_usd)
    if event_type:
        params["event_type"] = str(event_type).strip().lower()

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/wallet-metrics/whale-alerts",
        headers=headers,
        params=params,
        timeout=45,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", [])) if isinstance(payload, dict) else pd.DataFrame()
    last_modified = payload.get("last_modified") if isinstance(payload, dict) else None
    return df, last_modified


def get_sanctions_exposure_30d_chain(*, chain: str) -> tuple[pd.DataFrame, str | None]:
    """Return (D) sanctions exposure, last 30 days, from `/ae/sanctions-exposure`.

    Returns (df, last_modified). Data is token-level aggregates (direct/1-hop/2-hop).
    """
    try:
        return _cached_get_sanctions_exposure_30d_chain(chain=chain)
    except _ApiConfigError:
        return pd.DataFrame(), None
    except Exception as e:
        logger.exception("Error fetching sanctions exposure (30d): %s", e)
        st.error(f"Failed to fetch sanctions exposure: {e}")
        return pd.DataFrame(), None


@st.cache_data(ttl=3600)
def _cached_get_sanctions_exposure_30d_chain(*, chain: str) -> tuple[pd.DataFrame, str | None]:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/ae/sanctions-exposure",
        headers=headers,
        params={"chain": chain_param},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    last_modified = payload.get("last_modified")

    for c in (
        "direct_sanctioned_volume",
        "direct_sanctioned_tx_count",
        "one_hop_exposed_wallets",
        "one_hop_volume_with_sanctions",
        "two_hop_wallets_capped",
        "two_hop_volume_capped",
    ):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "token_symbol" in df.columns:
        df = df.sort_values("token_symbol", ascending=True, kind="mergesort")

    return df, last_modified


def get_last_updated(chain: str = "Ethereum") -> str:
    """Return last snapshot timestamp (Parquet-backed).

    NOTE: This is not the legacy `/dashboard/last-updated` timestamp.
    """
    try:
        return _cached_get_last_updated(chain=chain)
    except _ApiConfigError:
        return "Unknown"
    except Exception as e:
        logger.exception("Error fetching snapshot last updated: %s", e)
        return "Unknown"


@st.cache_data(ttl=3600)
def _cached_get_last_updated(*, chain: str = "Ethereum") -> str:
    api_url, api_key = _require_api_config()

    headers = {"X-API-Key": api_key}
    params = {"chain": _chain_to_param(chain)}
    resp = requests.get(f"{api_url}/dashboard/total-wallets-tracked", headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json() or {}

    timestamp = payload.get("asof_ts") or "Unknown"
    st.session_state["cloud_last_modified"] = f"{timestamp} (snapshot Parquet)"
    return timestamp


def get_dashboard_summary_chain(chain: str, hours: int = 24) -> dict:
    """Dashboard summary backed by the new snapshot Parquets.

    Uses the dedicated 1-row KPI snapshot (`/dashboard/total-wallets-tracked`).
    For non-24h windows, returns placeholders (no approximation).
    """
    if hours != 24:
        return {
            "total_volume": None,
            "unique_wallets": None,
            "average_risk_score": None,
            "total_transactions": None,
            "date_range": {"start": "N/A", "end": "N/A"},
            "_placeholder": True,
            "_note": "Only 24h KPI snapshots are available for the new Parquet pipeline.",
        }

    try:
        return _cached_get_dashboard_summary_chain(chain=chain)
    except _ApiConfigError:
        return {}
    except Exception as e:
        logger.exception("Error fetching snapshot KPI summary: %s", e)
        st.error(f"Failed to fetch snapshot KPI summary: {e}")
        return {}


@st.cache_data(ttl=3600)
def _cached_get_dashboard_summary_chain(*, chain: str) -> dict:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/total-wallets-tracked",
        headers=headers,
        params={"chain": chain_param},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json() or {}

    avg_priority = payload.get("avg_priority_score")
    if avg_priority is None:
        resp2 = requests.get(
            f"{api_url}/wallet-metrics/stats/summary",
            headers=headers,
            params={"chain": chain_param},
            timeout=30,
        )
        resp2.raise_for_status()
        summary = resp2.json() or {}
        avg_priority = (summary.get("priority_scores") or {}).get("average")

    asof_ts = payload.get("asof_ts")
    return {
        "total_volume": payload.get("total_volume_usd_24h"),
        "unique_wallets": payload.get("total_wallets"),
        "average_risk_score": avg_priority,
        "total_transactions": payload.get("total_tx_count_24h"),
        "date_range": {"start": asof_ts or "N/A", "end": asof_ts or "N/A"},
    }


def get_top_wallets_chain(chain: str, top_n: int = 100, sort_by: str = "risk", hours: int = 24) -> pd.DataFrame:
    """Top wallets table backed by snapshot Parquets.

    Uses `/wallet-metrics/top-risk` (priority_score) and returns an Advanced Overview-style schema.
    """
    try:
        return _cached_get_top_wallets_chain(chain=chain, top_n=top_n, sort_by=sort_by, hours=hours)
    except _ApiConfigError:
        return pd.DataFrame()
    except Exception as e:
        logger.exception("Error fetching snapshot top wallets: %s", e)
        st.error(f"Failed to fetch snapshot top wallets: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_get_top_wallets_chain(
    *,
    chain: str,
    top_n: int = 100,
    sort_by: str = "risk",
    hours: int = 24,
) -> pd.DataFrame:
    try:
        capped = int(top_n)
    except Exception:
        capped = 100
    capped = max(1, min(1000, capped))

    df = _cached_get_top_wallets_snapshot_raw(chain=chain, limit=capped)
    if df.empty:
        return pd.DataFrame()

    wallet_col = "wallet_address" if "wallet_address" in df.columns else ("wallet" if "wallet" in df.columns else None)
    priority_col = "priority_score" if "priority_score" in df.columns else None
    vol_col = "volume_24h" if "volume_24h" in df.columns else None
    tx_col = "tx_count_24h" if "tx_count_24h" in df.columns else None
    cp_col = "unique_counterparties_24h" if "unique_counterparties_24h" in df.columns else None

    if wallet_col is None:
        return pd.DataFrame()

    n = len(df)
    out = pd.DataFrame(
        {
            "Wallet": df[wallet_col].astype(str),
            "Priority Score": pd.to_numeric(df[priority_col], errors="coerce") if priority_col else pd.Series([None] * n),
            "24h Volume": pd.to_numeric(df[vol_col], errors="coerce") if vol_col else pd.Series([None] * n),
            "24h Txns": pd.to_numeric(df[tx_col], errors="coerce") if tx_col else pd.Series([None] * n),
            "Counterparties": pd.to_numeric(df[cp_col], errors="coerce") if cp_col else pd.Series([None] * n),
        }
    )

    sort_key = (sort_by or "risk").strip().lower()
    if sort_key == "volume":
        out = out.sort_values(["24h Volume", "Priority Score"], ascending=[False, False], na_position="last")
    else:
        out = out.sort_values(["Priority Score", "24h Volume"], ascending=[False, False], na_position="last")

    out = out.head(capped).copy()
    out.insert(0, "Rank", range(1, len(out) + 1))
    return out


def get_top_wallets_snapshot_raw(
    *,
    chain: str,
    limit: int = 1000,
    min_volume_24h: float = 0,
    anomaly_severity: str | None = None,
) -> pd.DataFrame:
    """Return raw rows from the Parquet-backed top priority wallets snapshot.

    This is used for click-through wallet analysis (all metrics), while the
    UI table may render a curated subset.
    """
    try:
        return _cached_get_top_wallets_snapshot_raw(
            chain=chain,
            limit=limit,
            min_volume_24h=min_volume_24h,
            anomaly_severity=anomaly_severity,
        )
    except _ApiConfigError:
        return pd.DataFrame()
    except Exception as e:
        logger.exception("Error fetching raw snapshot top wallets: %s", e)
        st.error(f"Failed to fetch snapshot top wallets: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_get_top_wallets_snapshot_raw(
    *,
    chain: str,
    limit: int = 1000,
    min_volume_24h: float = 0,
    anomaly_severity: str | None = None,
) -> pd.DataFrame:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    try:
        capped = int(limit)
    except Exception:
        capped = 1000
    capped = max(1, min(1000, capped))

    headers = {"X-API-Key": api_key}
    params = {
        "chain": chain_param,
        "limit": capped,
        "min_volume_24h": float(min_volume_24h or 0),
    }
    if anomaly_severity:
        params["anomaly_severity"] = str(anomaly_severity)

    def _fetch(p: dict) -> requests.Response:
        return requests.get(f"{api_url}/wallet-metrics/top-risk", headers=headers, params=p, timeout=60)

    resp = _fetch(params)
    if resp.status_code == 422 and int(params.get("limit") or 0) > 500:
        params2 = dict(params)
        params2["limit"] = 500
        resp = _fetch(params2)

    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        return pd.DataFrame()

    if "wallet_address" in df.columns:
        if chain_param == "eth":
            df["wallet_address"] = df["wallet_address"].astype(str).str.lower()
        else:
            df["wallet_address"] = df["wallet_address"].astype(str)

    return df


def get_rolling_metrics_snapshot_raw(
    *,
    chain: str,
    limit: int = 1000,
    order_by: str = "priority_score",
    order: str = "desc",
) -> tuple[pd.DataFrame, str | None]:
    """Return raw rows from the Parquet-backed rolling metrics snapshot.

    Backed by `/wallet-metrics/rolling` (retained top-1,000 snapshot).
    """
    try:
        return _cached_get_rolling_metrics_snapshot_raw(
            chain=chain,
            limit=limit,
            order_by=order_by,
            order=order,
        )
    except _ApiConfigError:
        return pd.DataFrame(), None
    except Exception as e:
        logger.exception("Error fetching rolling snapshot: %s", e)
        st.error(f"Failed to fetch rolling snapshot: {e}")
        return pd.DataFrame(), None


@st.cache_data(ttl=3600)
def _cached_get_rolling_metrics_snapshot_raw(
    *,
    chain: str,
    limit: int = 1000,
    order_by: str = "priority_score",
    order: str = "desc",
) -> tuple[pd.DataFrame, str | None]:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    try:
        capped = int(limit)
    except Exception:
        capped = 1000
    capped = max(1, min(1000, capped))

    headers = {"X-API-Key": api_key}
    params = {
        "chain": chain_param,
        "limit": capped,
        "order_by": str(order_by or "priority_score"),
        "order": str(order or "desc"),
    }
    resp = requests.get(f"{api_url}/wallet-metrics/rolling", headers=headers, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    asof_ts = payload.get("asof_ts")
    return df, asof_ts


def get_timeseries_data_chain(chain: str, hours: int = 24) -> pd.DataFrame:
    """Chain-level volume timeseries backed by snapshot Parquets (24h only)."""
    try:
        return _cached_get_timeseries_data_chain(chain=chain, hours=hours)
    except _ApiConfigError:
        return pd.DataFrame(columns=["datetime", "Token", "Volume"])
    except Exception as e:
        logger.exception("Error fetching snapshot timeseries: %s", e)
        st.error(f"Failed to fetch snapshot timeseries: {e}")
        return pd.DataFrame(columns=["datetime", "Token", "Volume"])


@st.cache_data(ttl=3600)
def _cached_get_timeseries_data_chain(*, chain: str, hours: int = 24) -> pd.DataFrame:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    if hours != 24:
        return pd.DataFrame(columns=["datetime", "Token", "Volume"])

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/timeseries-snapshot",
        headers=headers,
        params={"chain": chain_param, "hours": 24},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    rows = payload.get("data", payload if isinstance(payload, list) else [])
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["datetime", "Token", "Volume"])

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0.0)
    if "Token" not in df.columns:
        df["Token"] = "TOTAL"

    return df[["datetime", "Token", "Volume"]]


def get_lookup_priority_distribution_chain(
    chain: str, active_window: str = "24h"
) -> tuple[pd.DataFrame, str | None, int | None]:
    """Priority-score histogram (active-window) for the vol30d>=10k lookup snapshot."""
    try:
        return _cached_get_lookup_priority_distribution_chain(chain=chain, active_window=active_window)
    except _ApiConfigError:
        return pd.DataFrame(), None, None
    except Exception as e:
        logger.exception("Error fetching lookup priority distribution: %s", e)
        st.error(f"Failed to fetch lookup priority distribution: {e}")
        return pd.DataFrame(), None, None


@st.cache_data(ttl=3600)
def _cached_get_lookup_priority_distribution_chain(
    *,
    chain: str,
    active_window: str = "24h",
) -> tuple[pd.DataFrame, str | None, int | None]:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/wallet-metrics/rolling-lookup/priority-distribution",
        headers=headers,
        params={"chain": chain_param, "active_window": active_window},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    asof_ts = payload.get("asof_ts")
    row_count = payload.get("row_count")

    for c in ("bin_start", "bin_end", "wallet_count"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "bin_start" in df.columns:
        df = df.sort_values("bin_start", ascending=True)

    return df, asof_ts, int(row_count) if row_count is not None else None


def get_lookup_component_averages_chain(
    chain: str, active_window: str = "24h"
) -> tuple[pd.DataFrame, str | None, int | None]:
    """Average component scores (active-window) for the vol30d>=10k lookup snapshot."""
    try:
        return _cached_get_lookup_component_averages_chain(chain=chain, active_window=active_window)
    except _ApiConfigError:
        return pd.DataFrame(), None, None
    except Exception as e:
        logger.exception("Error fetching lookup component averages: %s", e)
        st.error(f"Failed to fetch lookup component averages: {e}")
        return pd.DataFrame(), None, None


@st.cache_data(ttl=3600)
def _cached_get_lookup_component_averages_chain(
    *,
    chain: str,
    active_window: str = "24h",
) -> tuple[pd.DataFrame, str | None, int | None]:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/wallet-metrics/rolling-lookup/component-averages",
        headers=headers,
        params={"chain": chain_param, "active_window": active_window},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    asof_ts = payload.get("asof_ts")
    row_count = payload.get("row_count")

    if "avg_score" in df.columns:
        df["avg_score"] = pd.to_numeric(df["avg_score"], errors="coerce")
    if "component" in df.columns:
        df["component"] = df["component"].astype(str)
        df = df.sort_values("component", ascending=True)

    return df, asof_ts, int(row_count) if row_count is not None else None


def get_token_volume_chain(chain: str, hours: int = 24) -> pd.DataFrame:
    """Token volume totals backed by snapshot Parquets (24h only)."""
    if hours != 24:
        return pd.DataFrame(columns=["Token", "Volume"])
    try:
        return _cached_get_token_volume_chain(chain=chain, hours=hours)
    except _ApiConfigError:
        return pd.DataFrame(columns=["Token", "Volume"])
    except Exception as e:
        logger.exception("Error fetching token volume snapshot: %s", e)
        st.error(f"Failed to fetch token volume: {e}")
        return pd.DataFrame(columns=["Token", "Volume"])


@st.cache_data(ttl=3600)
def _cached_get_token_volume_chain(*, chain: str, hours: int = 24) -> pd.DataFrame:
    api_url, api_key = _require_api_config()
    chain_param = _chain_to_param(chain)

    if hours != 24:
        return pd.DataFrame(columns=["Token", "Volume"])

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/token-volume-snapshot",
        headers=headers,
        params={"chain": chain_param, "hours": 24},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["Token", "Volume"])

    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0.0)
    if "Token" in df.columns:
        df["Token"] = df["Token"].astype(str)
    return df[["Token", "Volume"]]


def get_systemic_stablecoin_current() -> tuple[pd.DataFrame, str | None, str | None]:
    """Return latest per-coin systemic metrics from `/dashboard/stablecoin-systemic-current`."""
    try:
        return _cached_get_systemic_stablecoin_current()
    except _ApiConfigError:
        return pd.DataFrame(), None, None
    except Exception as e:
        logger.exception("Error fetching systemic current: %s", e)
        st.error(f"Failed to fetch systemic current: {e}")
        return pd.DataFrame(), None, None


@st.cache_data(ttl=600)
def _cached_get_systemic_stablecoin_current() -> tuple[pd.DataFrame, str | None, str | None]:
    api_url, api_key = _require_api_config()

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/stablecoin-systemic-current",
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    asof_ts = payload.get("asof_ts")
    last_modified = payload.get("last_modified")

    numeric_cols = [
        "price_usd_avg",
        "peg_deviation_pct_avg",
        "market_cap_usd_avg",
        "volume_24h_usd_avg",
        "net_issuance_24h_usd",
        "systemic_risk_score_0_100",
        "systemic_risk_confidence_0_100",
        "systemic_component_peg",
        "systemic_component_liquidity",
        "systemic_component_sell_pressure",
        "systemic_component_activity",
        "systemic_component_supply",
        "systemic_component_fragmentation",
        "anomaly_score_24h",
        "peg_stress_score",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "hour_ts" in df.columns:
        df["hour_ts"] = pd.to_datetime(df["hour_ts"], errors="coerce", utc=True)
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.upper()

    return df, asof_ts, last_modified


def get_systemic_stablecoin_summary() -> dict:
    """Return latest market-level systemic summary from `/dashboard/stablecoin-systemic-summary`."""
    try:
        return _cached_get_systemic_stablecoin_summary()
    except _ApiConfigError:
        return {}
    except Exception as e:
        logger.exception("Error fetching systemic summary: %s", e)
        st.error(f"Failed to fetch systemic summary: {e}")
        return {}


@st.cache_data(ttl=600)
def _cached_get_systemic_stablecoin_summary() -> dict:
    api_url, api_key = _require_api_config()

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/stablecoin-systemic-summary",
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    return payload if isinstance(payload, dict) else {}


def get_systemic_stablecoin_timeseries(
    *,
    symbol: str,
    hours: int = 168,
) -> tuple[pd.DataFrame, str | None, str | None]:
    """Return per-coin systemic timeseries from `/dashboard/stablecoin-systemic-timeseries`."""
    try:
        return _cached_get_systemic_stablecoin_timeseries(symbol=symbol, hours=hours)
    except _ApiConfigError:
        return pd.DataFrame(), None, None
    except Exception as e:
        logger.exception("Error fetching systemic timeseries: %s", e)
        st.error(f"Failed to fetch systemic timeseries: {e}")
        return pd.DataFrame(), None, None


@st.cache_data(ttl=600)
def _cached_get_systemic_stablecoin_timeseries(
    *,
    symbol: str,
    hours: int = 168,
) -> tuple[pd.DataFrame, str | None, str | None]:
    api_url, api_key = _require_api_config()
    token = str(symbol or "").strip().upper() or "USDT"

    headers = {"X-API-Key": api_key}
    resp = requests.get(
        f"{api_url}/dashboard/stablecoin-systemic-timeseries",
        headers=headers,
        params={"symbol": token, "hours": int(hours)},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    df = pd.DataFrame(payload.get("data", []))
    asof_ts = payload.get("asof_ts")
    last_modified = payload.get("last_modified")

    if "hour_ts" in df.columns:
        df["hour_ts"] = pd.to_datetime(df["hour_ts"], errors="coerce", utc=True)
    for col in (
        "price_usd_avg",
        "peg_deviation_pct_avg",
        "systemic_risk_score_0_100",
        "systemic_risk_confidence_0_100",
        "anomaly_score_24h",
        "peg_stress_score",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if not df.empty and "hour_ts" in df.columns:
        df = df.sort_values("hour_ts", ascending=True, kind="mergesort")

    return df, asof_ts, last_modified


def get_wallet_lookup_parquet(*, chain: str, wallet_address: str) -> dict | None:
    """Lookup a wallet in the large vol30d>=10k Parquet snapshot via API.

    Uses `POST /wallet-metrics/wallet-parquet` on the Cloud Run API.
    Returns the API payload dict, or None if not found / unavailable.

    NOTE: Transient errors (503, 502, timeouts) raise so that
    ``@st.cache_data`` does **not** cache the failure.  Only a definitive
    404 (wallet genuinely absent) is cached as ``None``.
    """
    try:
        return _cached_get_wallet_lookup_parquet(chain=chain, wallet_address=wallet_address)
    except _ApiConfigError:
        return None


@st.cache_data(ttl=600)
def _cached_get_wallet_lookup_parquet(*, chain: str, wallet_address: str) -> dict | None:
    api_url, api_key = _require_api_config()

    chain_param = _chain_to_param(chain)
    wallet_raw = (wallet_address or "").strip()
    if not wallet_raw:
        return None

    _MAX_RETRIES = 2
    _RETRY_DELAY = 3  # seconds – enough for Cloud Run cold starts

    import time as _time

    headers = {"X-API-Key": api_key}
    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{api_url}/wallet-metrics/wallet-parquet",
                headers=headers,
                params={"chain": chain_param},
                json={"wallet_address": wallet_raw},
                timeout=45,
            )

            # Definitive "not found" → cache as None.
            if resp.status_code == 404:
                return None

            # Transient server errors → retry (Cloud Run cold-start 503, etc.)
            if resp.status_code in {502, 503, 504}:
                logger.warning(
                    "Transient %s from wallet-parquet (attempt %d/%d) for %s",
                    resp.status_code, attempt, _MAX_RETRIES, wallet_raw,
                )
                last_exc = requests.exceptions.HTTPError(
                    f"{resp.status_code} from wallet-parquet", response=resp,
                )
                if attempt < _MAX_RETRIES:
                    _time.sleep(_RETRY_DELAY)
                continue

            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else None

        except requests.exceptions.HTTPError:
            raise  # propagate so @st.cache_data does NOT cache the error
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning(
                "Transient network error (attempt %d/%d) for wallet-parquet: %s",
                attempt, _MAX_RETRIES, e,
            )
            last_exc = e
            if attempt < _MAX_RETRIES:
                _time.sleep(_RETRY_DELAY)
            continue
        except Exception as e:
            logger.exception("Unexpected error fetching parquet wallet lookup: %s", e)
            raise  # don't cache unexpected errors either

    # All retries exhausted – raise so the failure is NOT cached.
    logger.error("All %d retries exhausted for wallet-parquet lookup: %s", _MAX_RETRIES, wallet_raw)
    raise last_exc or RuntimeError("wallet-parquet lookup failed after retries")
