import streamlit as st
import logging

from utils.formatting import format_relative_time

logger = logging.getLogger(__name__)


def sidebar(last_updated=None, show_chain_toggle: bool = False):
    if "chain" not in st.session_state:
        st.session_state["chain"] = "Ethereum"

    if show_chain_toggle:
        chain = st.sidebar.selectbox(
            "Chain",
            options=["Ethereum", "Tron"],
            index=0 if st.session_state.get("chain") != "Tron" else 1,
        )
        if chain != st.session_state.get("chain"):
            st.session_state["chain"] = chain
            st.rerun()

    st.sidebar.caption(
        "This dashboard monitors stablecoin activity and AML-related risk signals."
    )

    if last_updated:
        pretty_last_updated = format_relative_time(last_updated, fallback=str(last_updated))
        st.sidebar.caption(f":material/access_time: **Last Updated:** {pretty_last_updated}")

    if st.sidebar.button("Refresh data"):
        try:
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            logger.exception("Error clearing cache: %s", e)
            st.sidebar.error(f"Failed to clear data cache: {e}")

    return None