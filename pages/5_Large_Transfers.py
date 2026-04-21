import pandas as pd
import streamlit as st

from utils.formatting import format_relative_time, format_volume, format_volume_exact
from utils.load_data_new import get_whale_alerts, get_whale_alert_tokens
from utils.sidebar import sidebar
from utils.styling import inject_icon_styles

RESULTS_LIMIT = 500

SHOW_OPTIONS = [25, 50, 100, 250, 500]

_CACHE_DF_KEY = "_large_transfers_cached_df_display"
_CACHE_TS_KEY = "_large_transfers_cached_sidebar_ts"
_CACHE_FILTERS_KEY = "_large_transfers_cached_filters"


def _chain_param_from_choice(chain_choice: str | None) -> str | None:
    """Map a UI label to the API's expected chain param (eth|tron)."""
    if not chain_choice:
        return None
    s = str(chain_choice).strip().lower()
    if not s or s == "all":
        return None
    if s in {"eth", "ethereum", "ethereum mainnet", "ethereum (mainnet)"}:
        return "eth"
    if s in {"tron", "trx"}:
        return "tron"
    # Best-effort fallback for custom labels (e.g. "ETH", "ETHEREUM", "TRON")
    if "eth" in s:
        return "eth"
    if "tron" in s or "trx" in s:
        return "tron"
    return None


def _get_tokens() -> list[str]:
    tokens, _last_modified = get_whale_alert_tokens(limit=2000)
    return tokens or []


def _get_alerts(
    chain: str | None,
    token: str | None,
    min_amount_usd: float | None,
    tx_type: str | None,
) -> tuple[int, dict | None, str | None]:
    params: dict[str, object] = {"limit": RESULTS_LIMIT}
    if chain:
        params["chain"] = chain
    if token:
        params["token_symbol"] = token
    if min_amount_usd is not None and min_amount_usd > 0:
        params["min_amount_usd"] = float(min_amount_usd)
    if tx_type and tx_type != "All":
        params["event_type"] = str(tx_type).strip().lower()

    try:
        df, last_modified = get_whale_alerts(
            chain=str(chain) if chain else None,
            token_symbol=str(token) if token else None,
            min_amount_usd=float(min_amount_usd) if min_amount_usd is not None else None,
            event_type=str(params.get("event_type")) if params.get("event_type") else None,
            days=30,
            limit=int(params.get("limit") or RESULTS_LIMIT),
        )
        payload = {
            "count": int(len(df)) if isinstance(df, pd.DataFrame) else 0,
            "last_modified": last_modified,
            "data": df.to_dict("records") if isinstance(df, pd.DataFrame) and not df.empty else [],
        }
        return 200, payload, None
    except Exception as e:
        return 0, None, f"Request failed: {e}"


def _get_latest_alert_timestamp() -> str | None:
    try:
        df, _last_modified = get_whale_alerts(days=30, limit=1)
        if df is None or df.empty or "block_timestamp" not in df.columns:
            return None
        ts = pd.to_datetime(df["block_timestamp"], utc=True, errors="coerce")
        if ts.notna().any():
            return ts.max().strftime("%Y-%m-%dT%H:%M:%SZ")
        return None
    except Exception:
        return None


st.set_page_config(
    page_title="Large Transfers - Stablecoin Risk Monitor",
    page_icon="🐋",
    layout="wide",
)

inject_icon_styles()

fallback_last_updated = _get_latest_alert_timestamp()

st.title("Large Transfers")

tokens = _get_tokens()

with st.container(border=True):
    col1, col2, col3, col4, col5 = st.columns([0.9, 1.1, 0.9, 1.1, 0.6])
    with col1:
        chain_choice = st.selectbox(
            "Chain",
            options=["All", "Ethereum", "Tron"],
            index=0,
        )

    with col2:
        token_choice = st.selectbox(
            "Token",
            options=["All"] + tokens,
            index=0,
        )
    with col3:
        tx_type_choice = st.selectbox(
            "Type",
            options=["All", "Mint", "Burn", "Issue", "Redeem", "Transfer"],
            index=0,
        )

    with col4:
        min_amt = st.number_input(
            "Min size (USD)",
            min_value=1_000_000.0,
            value=10_000_000.0,
            step=1_000_000.0,
        )

    with col5:
        st.write("")
        submitted = st.button("View", type="primary")

cached_df_display = st.session_state.get(_CACHE_DF_KEY)
cached_sidebar_ts = st.session_state.get(_CACHE_TS_KEY)
cached_filters = st.session_state.get(_CACHE_FILTERS_KEY) or {}

# Default: fetch once on first page load (with the default $10M threshold)
autofetch = (not bool(st.session_state.get("_large_transfers_autofetch_done"))) and cached_df_display is None
should_fetch = submitted or autofetch

# Sidebar freshness: when cached results exist, reuse their timestamp; otherwise
# fall back to the newest alert timestamp.
sidebar_ts = cached_sidebar_ts or fallback_last_updated

status = 0
payload = None
err = None

if should_fetch:
    chain_param = _chain_param_from_choice(chain_choice)
    token_param = None if token_choice == "All" else token_choice

    with st.spinner("Loading whale alerts…"):
        status, payload, err = _get_alerts(chain_param, token_param, min_amt, tx_type_choice)

    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list) and data:
            df_sidebar = pd.DataFrame(data)
            if "block_timestamp" in df_sidebar.columns:
                ts = pd.to_datetime(df_sidebar["block_timestamp"], utc=True, errors="coerce")
                if ts.notna().any():
                    sidebar_ts = ts.max().strftime("%Y-%m-%dT%H:%M:%SZ")

sidebar(last_updated=sidebar_ts, show_chain_toggle=False)


def _build_transfers_title(filters: dict) -> str:
    title_token = filters.get("token", "All")
    title_type = filters.get("type", "All")
    title_chain = filters.get("chain", "All")
    title_min_amt = filters.get("min_amt")

    token_prefix = "" if title_token == "All" else f"{title_token} "
    type_prefix = "" if title_type == "All" else f"{title_type} "
    amount_suffix = (
        f" above {format_volume(float(title_min_amt))}"
        if title_min_amt is not None and float(title_min_amt) > 0
        else ""
    )
    chain_suffix = f" on {title_chain}" if title_chain in {"Ethereum", "Tron"} else ""
    return f"{token_prefix}{type_prefix}Transfers{amount_suffix}{chain_suffix}".strip()


transfers_box = st.container(border=True)
with transfers_box:
    col_title, col_ctrl = st.columns([3, 1], vertical_alignment="center")
    with col_title:
        title_slot = st.empty()
        title_slot.subheader(_build_transfers_title(cached_filters))
    with col_ctrl:
        label_col, select_col = st.columns([1, 3], vertical_alignment="center")
        with label_col:
            st.caption("Show")
        with select_col:
            current_show = int(st.session_state.get("large_transfers_show", 100) or 100)
            show_n = st.selectbox(
                "Rows to show",
                options=SHOW_OPTIONS,
                index=SHOW_OPTIONS.index(current_show) if current_show in SHOW_OPTIONS else SHOW_OPTIONS.index(100),
                key="large_transfers_show",
                label_visibility="collapsed",
            )

if should_fetch:
    if err:
        if status == 0:
            st.error(err)
        else:
            st.error(f"API error ({status}): {err}")
        st.stop()

    # Update the title immediately on the same run as the click/autofetch.
    fresh_title_filters = {
        "chain": chain_choice,
        "token": token_choice,
        "type": tx_type_choice,
        "min_amt": float(min_amt) if min_amt is not None else None,
    }
    title_slot.subheader(_build_transfers_title(fresh_title_filters))

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data:
        with transfers_box:
            st.info("No transactions found for the selected filters.")
        st.stop()

    df = pd.DataFrame(data)
    if "amount_usd" in df.columns:
        try:
            df["amount_usd"] = pd.to_numeric(df["amount_usd"], errors="coerce")
        except Exception:
            pass

    # Derive a stable tx type label (Mint/Burn/Issue/Redeem/Transfer)
    if any(c in df.columns for c in {"is_mint", "is_burn", "is_issue", "is_redeem"}):
        is_mint = df.get("is_mint")
        is_burn = df.get("is_burn")
        is_issue = df.get("is_issue")
        is_redeem = df.get("is_redeem")
        df["_tx_type"] = "Transfer"
        if is_mint is not None:
            df.loc[is_mint.fillna(False).astype(bool), "_tx_type"] = "Mint"
        if is_burn is not None:
            df.loc[is_burn.fillna(False).astype(bool), "_tx_type"] = "Burn"
        if is_issue is not None:
            df.loc[is_issue.fillna(False).astype(bool), "_tx_type"] = "Issue"
        if is_redeem is not None:
            df.loc[is_redeem.fillna(False).astype(bool), "_tx_type"] = "Redeem"
    elif "event_type" in df.columns:
        df["_tx_type"] = df["event_type"].astype(str).str.strip().str.lower().map(
            {
                "mint": "Mint",
                "burn": "Burn",
                "issue": "Issue",
                "redeem": "Redeem",
                "transfer": "Transfer",
            }
        )
        df["_tx_type"] = df["_tx_type"].fillna("Transfer")
    else:
        df["_tx_type"] = "Transfer"

    # Apply client-side type filter
    if tx_type_choice != "All":
        df = df[df["_tx_type"] == tx_type_choice]
        if df.empty:
            with transfers_box:
                st.info("No transactions found for the selected filters.")
            st.stop()

    if "block_timestamp" in df.columns:
        df["_time"] = df["block_timestamp"].apply(format_relative_time)

    if "chain" in df.columns:
        chain_norm = df["chain"].astype(str).str.strip().str.lower()
        df["chain"] = chain_norm.map({"eth": "Ethereum", "tron": "Tron"}).fillna(df["chain"].astype(str))

    # Build a clean display table (hide internal fields + rename columns)
    hidden_cols = {
        "whale_bucket",
        "token_address",
        "is_mint",
        "is_burn",
        "is_issue",
        "is_redeem",
    }
    display_cols = [
        "_time",
        "chain",
        "token_symbol",
        "_tx_type",
        "amount_usd",
        "from_address",
        "to_address",
        "transaction_hash",
    ]

    cols_present = [c for c in display_cols if c in df.columns]
    df_display = df[cols_present].copy()
    for c in list(hidden_cols):
        if c in df_display.columns:
            df_display = df_display.drop(columns=[c])

    df_display = df_display.rename(
        columns={
            "_time": "Time",
            "chain": "Chain",
            "token_symbol": "Token",
            "_tx_type": "Type",
            "amount_usd": "Amount",
            "from_address": "From",
            "to_address": "To",
            "transaction_hash": "Transaction Hash",
        }
    )

    if "Amount" in df_display.columns:
        try:
            amount_numeric = pd.to_numeric(df_display["Amount"], errors="coerce")
            df_display["Amount"] = amount_numeric.apply(
                lambda v: format_volume_exact(float(v)) if pd.notna(v) else ""
            )
        except Exception:
            pass

    # Cache results so navigating away/back doesn't require a hard refresh.
    st.session_state[_CACHE_DF_KEY] = df_display
    st.session_state[_CACHE_TS_KEY] = sidebar_ts
    st.session_state[_CACHE_FILTERS_KEY] = {
        "chain": chain_choice,
        "token": token_choice,
        "type": tx_type_choice,
        "min_amt": float(min_amt) if min_amt is not None else None,
    }
    st.session_state["_large_transfers_autofetch_done"] = True

    with transfers_box:
        st.dataframe(df_display.head(int(show_n)), use_container_width=True, hide_index=True)

elif isinstance(cached_df_display, pd.DataFrame) and not cached_df_display.empty:
    with transfers_box:
        st.dataframe(cached_df_display.head(int(show_n)), use_container_width=True, hide_index=True)

