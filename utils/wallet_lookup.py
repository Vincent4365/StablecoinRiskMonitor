import re
from typing import Any, Optional

import streamlit as st


def _is_valid_eth_address(addr: str) -> bool:
	a = (addr or "").strip().lower()
	return bool(re.fullmatch(r"^0x[a-f0-9]{40}$", a))


def _is_valid_tron_address(addr: str) -> bool:
	a = (addr or "").strip()
	if not a:
		return False

	# TRON base58check addresses typically start with 'T' and are 34 chars.
	# Accept common base58 alphabet (no 0/O/I/l).
	if re.fullmatch(r"^T[1-9A-HJ-NP-Za-km-z]{33}$", a):
		return True

	# TRON hex addresses are often represented as 21 bytes starting with 0x41 (or 41).
	if re.fullmatch(r"^(0x)?41[0-9a-fA-F]{40}$", a):
		return True

	return False


def _set_query_params(params: dict[str, str]) -> None:
	"""Best-effort query param setter for Streamlit new+legacy APIs."""
	try:
		# Streamlit >= 1.30
		for k, v in params.items():
			st.query_params[k] = v
		return
	except Exception:
		pass

	try:
		st.experimental_set_query_params(**params)
	except Exception:
		# If we can't set the URL, at least keep session state in sync.
		return


def render_wallet_details_lookup(
	*,
	default_wallet: str,
	default_chain_label: str,
	help_text: bool = True,
) -> tuple[str, str]:
	"""Render a small wallet lookup/navigator for the Wallet Analysis page.

	Returns (chain_param, wallet_address). If the user submits, the function updates
	query params + session_state and reruns.
	"""
	default_chain = "Tron" if str(default_chain_label or "").strip().lower() == "tron" else "Ethereum"

	# Avoid double borders: Streamlit may outline forms, so don't add an extra container border.
	with st.container(border=False):
		# Hide Streamlit's input instruction text (e.g., "Press Enter to apply").
		st.markdown(
			"""
			<style>
			[data-testid="InputInstructions"] { display: none !important; }
			div[data-testid="stTextInput"] small { display: none !important; }
			div[data-testid="stForm"] small { display: none !important; }
			</style>
			""",
			unsafe_allow_html=True,
		)
		with st.form(key="wallet_details_lookup_form", clear_on_submit=False):
			c1, c2, c3 = st.columns([1.2, 4.0, 1.2], vertical_alignment="center")
			with c1:
				chain_label = st.selectbox(
					"Chain",
					options=["Ethereum", "Tron"],
					index=0 if default_chain != "Tron" else 1,
					key="wallet_details_lookup_chain",
					label_visibility="collapsed",
				)
			with c2:
				if chain_label == "Tron":
					placeholder = "T… (or 41… / 0x41…)"
					h = "TRON: base58 (T… 34 chars) or hex (41… / 0x41…)" if help_text else None
				else:
					placeholder = "0x…"
					h = "Ethereum: must match ^0x[a-f0-9]{40}$" if help_text else None

				wallet_input = st.text_input(
					"Wallet address",
					value=str(default_wallet or ""),
					placeholder=placeholder,
					help=h,
					key="wallet_details_lookup_wallet",
					label_visibility="collapsed",
				)
			with c3:
				submitted = st.form_submit_button(
					"View",
					use_container_width=True,
					type="primary",
				)

	chain_param = "tron" if chain_label == "Tron" else "eth"
	wallet_raw = (wallet_input or "").strip()

	if submitted:
		if not wallet_raw:
			st.error("Enter a wallet address.")
			st.stop()

		if chain_param == "tron":
			if not _is_valid_tron_address(wallet_raw):
				st.error("Invalid TRON address.")
				st.stop()
			wallet_norm = wallet_raw
		else:
			wallet_norm = wallet_raw.lower()
			if not _is_valid_eth_address(wallet_norm):
				st.error("Invalid Ethereum address.")
				st.stop()

		st.session_state["wallet_details_wallet"] = wallet_norm
		st.session_state["wallet_details_chain"] = chain_param
		st.session_state["wallet_details_source"] = "lookup"
		# Clear any cached row from a previous wallet to avoid double-click reverts.
		st.session_state.pop("wallet_details_snapshot_row", None)
		# Do not rewrite query params here; multipage URL/query-state can be flaky and
		# can cause the page to revert to an older linked wallet on subsequent submits.
		st.rerun()

	# Non-submitted: return the current defaults.
	wallet_out = wallet_raw.lower() if chain_param == "eth" else wallet_raw
	return chain_param, wallet_out