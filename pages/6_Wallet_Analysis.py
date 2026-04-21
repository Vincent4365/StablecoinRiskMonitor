import pandas as pd
import streamlit as st

from datetime import datetime, timezone

from utils.load_data_new import get_last_updated, get_top_wallets_snapshot_raw, get_wallet_lookup_parquet
from utils.sidebar import sidebar
from utils.styling import inject_icon_styles
from utils.formatting import format_volume, format_relative_time, format_utc_timestamp
from utils.wallet_lookup import render_wallet_details_lookup


def _get_query_params() -> dict:
	try:
		# New API (Streamlit >= 1.30)
		return dict(st.query_params)
	except Exception:
		# Legacy API
		return st.experimental_get_query_params()


def _normalize_chain_param(chain: str | None) -> tuple[str, str]:
	c = (chain or "").strip().lower()
	if c in {"tron", "trx"}:
		return "tron", "Tron"
	return "eth", "Ethereum"


def _pretty_metric_name(key: str) -> str:
	if not key:
		return ""

	# Common explicit mappings first.
	explicit = {
		"asof_ts": "As of (UTC)",
		"wallet_address": "Wallet",
		"priority_score": "Priority Score",
		"risk_level": "Risk Level",
		"exchange_like_flag": "Exchange-like",
		"raw_priority": "Raw Priority",
		"raw_priority_adj": "Raw Priority (Adj)",
		"volume_24h": "Volume (24h)",
		"tx_count_24h": "Transactions (24h)",
		"unique_counterparties_24h": "Counterparties (24h)",
		"source": "Source",
		"snapshot_age_seconds": "Snapshot Age (seconds)",
	}
	if key in explicit:
		return explicit[key]

	# Suffix/pattern-based prettification.
	if key.endswith("_ratio_30d"):
		base = key[: -len("_ratio_30d")]
		return f"{_pretty_metric_name(base)} Ratio (30d)"
	if key.endswith("_ratio"):
		base = key[: -len("_ratio")]
		return f"{_pretty_metric_name(base)} Ratio"
	if key.endswith("_score"):
		base = key[: -len("_score")]
		return f"{_pretty_metric_name(base)} Score"

	# Generic: snake_case -> Title Case with a few acronym fixes.
	parts = [p for p in str(key).strip().split("_") if p]
	pretty_parts: list[str] = []
	for p in parts:
		pl = p.lower()
		if pl in {"usd", "eth", "trx", "usdt", "usdc", "dai", "usde"}:
			pretty_parts.append(p.upper())
			continue
		if pl in {"24h", "30d", "7d"}:
			pretty_parts.append(pl)
			continue
		if pl in {"tx", "txn", "txns"}:
			pretty_parts.append("Tx")
			continue
		pretty_parts.append(pl.capitalize())

	name = " ".join(pretty_parts)
	name = name.replace(" 24h", " (24h)").replace(" 30d", " (30d)")
	return name



def _as_rows(record: dict, keys: list[str]) -> pd.DataFrame:
	rows = []
	for k in keys:
		if k in record:
			v = record.get(k)
			# Keep volume fields consistent with dashboard formatting.
			if v is not None and isinstance(k, str) and (k.startswith("volume_") or k.endswith("_volume") or "volume" in k):
				try:
					v = format_volume(float(v))
				except Exception:
					pass
			rows.append({"Metric": _pretty_metric_name(str(k)), "Value": "" if v is None else str(v)})
	return pd.DataFrame(rows, columns=["Metric", "Value"])


def _flatten_wallet_parquet_payload(payload: dict) -> dict:
	"""Flatten POST /wallet-metrics/wallet-parquet response into a row-like dict."""
	row: dict = {}
	row["wallet_address"] = payload.get("wallet_address")
	row["exchange_like_flag"] = payload.get("exchange_like_flag")
	row["priority_score"] = payload.get("priority_score")
	row["risk_level"] = payload.get("risk_level")
	row["snapshot_age_seconds"] = payload.get("snapshot_age_seconds")
	row["source"] = payload.get("source")

	# Derive asof_ts from snapshot_age_seconds (API doesn't currently return asof_ts).
	try:
		age_s = int(payload.get("snapshot_age_seconds") or 0)
		asof_dt = datetime.now(timezone.utc) - pd.Timedelta(seconds=max(age_s, 0))
		row["asof_ts"] = asof_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
	except Exception:
		row["asof_ts"] = None

	scores = payload.get("scores")
	if isinstance(scores, dict):
		for k, v in scores.items():
			row[str(k)] = v

	metrics = payload.get("metrics")
	if isinstance(metrics, dict):
		for k, v in metrics.items():
			row[str(k)] = v

	return row


st.set_page_config(
	page_title="Wallet Analysis - Stablecoin Risk Monitor",
	page_icon="💱",
	layout="wide",
)

inject_icon_styles()

params = _get_query_params()
wallet_from_params = ""
if isinstance(params, dict):
	w = params.get("wallet")
	if isinstance(w, list):
		wallet_from_params = (w[0] if w else "")
	else:
		wallet_from_params = w or ""

chain_param_from_params = ""
if isinstance(params, dict):
	c = params.get("chain")
	if isinstance(c, list):
		chain_param_from_params = (c[0] if c else "")
	else:
		chain_param_from_params = c or ""

# Treat URL query params as a navigation seed.
# Apply them only when they actually change (e.g., a new click-through from 1B),
# so in-page lookups don't get overwritten by a stale URL.
seen_qp_wallet = st.session_state.get("_wallet_details_seen_qp_wallet")
seen_qp_chain = st.session_state.get("_wallet_details_seen_qp_chain")

qp_chain_param, _qp_chain_label = _normalize_chain_param(chain_param_from_params)
qp_wallet_raw = (wallet_from_params or "").strip()
qp_wallet_norm = qp_wallet_raw.lower() if qp_chain_param == "eth" else qp_wallet_raw

nav_changed = False
if chain_param_from_params and str(chain_param_from_params) != str(seen_qp_chain or ""):
	nav_changed = True
if qp_wallet_raw and str(qp_wallet_raw) != str(seen_qp_wallet or ""):
	nav_changed = True

# Always remember what URL params we last saw.
if chain_param_from_params:
	st.session_state["_wallet_details_seen_qp_chain"] = chain_param_from_params
if qp_wallet_raw:
	st.session_state["_wallet_details_seen_qp_wallet"] = qp_wallet_raw

if nav_changed or not (st.session_state.get("wallet_details_wallet") or "").strip():
	if chain_param_from_params:
		st.session_state["wallet_details_chain"] = qp_chain_param
	if qp_wallet_raw:
		st.session_state["wallet_details_wallet"] = qp_wallet_norm
		st.session_state["wallet_details_source"] = "params"
	st.session_state.pop("wallet_details_snapshot_row", None)

chain_for_last_updated = "Tron" if str(st.session_state.get("wallet_details_chain") or "").strip().lower() == "tron" else "Ethereum"
last_updated = get_last_updated(chain=chain_for_last_updated)
sidebar(last_updated, show_chain_toggle=False)

st.title("Wallet Analysis")

# Wallet lookup / navigation (prefilled from query params when present)
_wallet_default = st.session_state.get("wallet_details_wallet", "") or ""
_chain_default_raw = st.session_state.get("wallet_details_chain", "") or ""
_chain_default_param, _chain_default_label = _normalize_chain_param(_chain_default_raw)
render_wallet_details_lookup(default_wallet=_wallet_default, default_chain_label=_chain_default_label)

# Re-read after the lookup widget (it may set session_state and trigger reruns).
wallet = st.session_state.get("wallet_details_wallet", "") or ""
chain_param_raw = st.session_state.get("wallet_details_chain", "") or ""
chain_param, chain_label = _normalize_chain_param(chain_param_raw)

wallet_str = (wallet or "").strip()
if not wallet_str:
	st.stop()

wallet_norm = wallet_str.strip().lower() if chain_param == "eth" else wallet_str.strip()

# Prefer the snapshot row passed from the dashboard click-through (no network re-fetch).
row = st.session_state.get("wallet_details_snapshot_row")
row_wallet = None
if isinstance(row, dict):
	row_wallet_raw = str(row.get("wallet_address", "")).strip() if row.get("wallet_address") is not None else ""
	row_wallet = row_wallet_raw.lower() if chain_param == "eth" else row_wallet_raw
	if chain_param == "eth":
		if str(row_wallet).lower() != str(wallet_norm).lower():
			row = None
	else:
		if str(row_wallet) != str(wallet_norm):
			row = None

if row is None:
	# Fallback: load the raw snapshot and filter.
	df = get_top_wallets_snapshot_raw(chain=chain_label, limit=1000)
	if df is None or df.empty or "wallet_address" not in df.columns:
		st.error("No snapshot data available.")
		st.stop()
	if chain_param == "eth":
		match = df[df["wallet_address"].astype(str).str.lower() == str(wallet_norm).lower()]
	else:
		match = df[df["wallet_address"].astype(str) == str(wallet_norm)]
	if match.empty:
		# Fallback: parquet-backed lookup across the large vol30d>=10k snapshot.
		try:
			payload = get_wallet_lookup_parquet(chain=chain_label, wallet_address=wallet_str)
		except Exception:
			# Transient API error (503 cold-start, timeout, etc.) – not cached.
			payload = None
			st.warning("Wallet lookup timed out (the API may be warming up). Please try again in a few seconds.")
			st.stop()
		if not payload:
			st.error(
				"Wallet not found in the current dataset. It may be inactive for the tracked stablecoins over the last 30 days, "
				"or its 30-day stablecoin volume is below \\$10,000."
			)
			st.stop()
		row = _flatten_wallet_parquet_payload(payload)
		st.session_state["wallet_details_snapshot_row"] = row
	else:
		row = match.iloc[0].to_dict()

asof_ts = row.get("asof_ts")

if asof_ts:
	snapshot_display = f"{format_utc_timestamp(asof_ts, fallback=str(asof_ts))} ({format_relative_time(asof_ts, fallback=str(asof_ts))})"
else:
	snapshot_display = "Unknown"

st.caption(f"Chain: {chain_label} | Wallet: {wallet_str} | Snapshot taken: {snapshot_display}")

# Key metrics
with st.container(border=True):
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		ps = row.get("priority_score")
		st.metric("Priority Score", "" if ps is None else f"{float(ps):.2f}")
	with col2:
		v = row.get("volume_24h")
		st.metric("24h Volume", "" if v is None else format_volume(float(v)))
	with col3:
		tx = row.get("tx_count_24h")
		st.metric("24h Transactions", "" if tx is None else f"{int(float(tx)):,}")
	with col4:
		cp = row.get("unique_counterparties_24h")
		st.metric("24h Counterparties", "" if cp is None else f"{int(float(cp)):,}")

# Organize fields
core_keys = [
	"asof_ts",
	"wallet_address",
	"priority_score",
	"exchange_like_flag",
	"raw_priority",
	"raw_priority_adj",
]

score_keys = sorted([k for k in row.keys() if k.endswith("_score") and k != "priority_score"], key=str)
ratio_keys = sorted([k for k in row.keys() if k.endswith("_ratio_30d") or k.startswith("volume_ratio_") or k.startswith("tx_ratio_")], key=str)
metric_keys = sorted(
	[
		k
		for k in row.keys()
		if k not in set(core_keys + score_keys + ratio_keys)
		and not k.endswith("_score")
	],
	key=str,
)

with st.container(border=True):
	st.subheader("Scores")
	base = _as_rows(row, ["priority_score", "raw_priority", "raw_priority_adj", "exchange_like_flag"])
	scores = _as_rows(row, score_keys)
	out = pd.concat([base, scores], ignore_index=True) if not scores.empty else base
	st.dataframe(
		out,
		hide_index=True,
		use_container_width=True,
		column_config={
			"Metric": st.column_config.TextColumn("Metric", width="medium"),
			"Value": st.column_config.TextColumn("Value", width="medium"),
		},
	)

with st.container(border=True):
	st.subheader("Ratios")
	ratios = _as_rows(row, ratio_keys)
	if ratios.empty:
		st.info("No ratio fields in snapshot.")
	else:
		st.dataframe(
			ratios,
			hide_index=True,
			use_container_width=True,
			column_config={
				"Metric": st.column_config.TextColumn("Metric", width="medium"),
				"Value": st.column_config.TextColumn("Value", width="medium"),
			},
		)

with st.container(border=True):
	st.subheader("All Metrics")
	metrics = _as_rows(row, metric_keys)
	st.dataframe(
		metrics,
		hide_index=True,
		use_container_width=True,
		column_config={
			"Metric": st.column_config.TextColumn("Metric", width="medium"),
			"Value": st.column_config.TextColumn("Value", width="medium"),
		},
	)

col_meth_left, col_meth_right = st.columns([3, 1], vertical_alignment="center")
with col_meth_right:
	if st.button("Methodology & Disclaimers", use_container_width=True):
		if hasattr(st, "switch_page"):
			st.switch_page("pages/8_Methodology.py")
		else:
			st.info("Open 'Methodology' from the page list.")

