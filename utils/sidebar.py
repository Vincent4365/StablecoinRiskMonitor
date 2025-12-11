import streamlit as st
import logging

logger = logging.getLogger(__name__)


def sidebar(last_updated=None):
    st.sidebar.caption(
        "This dashboard monitors stablecoin activity and AML-related risk signals. "
        "All blockchain addresses have been anonymized to ensure privacy."
    )

    if last_updated:
        st.sidebar.caption(f":material/access_time: **Last Updated:** {last_updated}")

    if st.sidebar.button("Refresh data"):
        try:
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            logger.exception("Error clearing cache: %s", e)
            st.sidebar.error(f"Failed to clear data cache: {e}")

    return None