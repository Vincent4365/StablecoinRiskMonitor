import streamlit as st
import logging

logger = logging.getLogger(__name__)


def sidebar():
    """Minimal sidebar for cloud-only mode.

    Keeps a short caption and exposes a manual cache-clear button so
    users can force a fresh cloud CSV fetch.
    """
    st.sidebar.caption(
        "This dashboard monitors stablecoin activity and AML-related risk signals. "
        "All blockchain addresses have been anonymized to ensure privacy."
    )

    # Restore persisted cloud last-updated time (if available) so caption survives reloads
    try:
        if "cloud_last_modified" not in st.session_state:
            from pathlib import Path

            cache_path = Path(__file__).parent.parent / ".cache" / "cloud_last_modified.txt"
            if cache_path.exists():
                try:
                    ts = cache_path.read_text().strip()
                except (OSError, UnicodeDecodeError) as e:
                    logger.warning("Failed to read cloud_last_modified cache: %s", e)
                else:
                    if ts:
                        st.session_state["cloud_last_modified"] = ts
    except ImportError:
        # Very unlikely: pathlib import failure — log and continue
        logger.warning("Pathlib import failed while restoring cache")

    if st.sidebar.button("Refresh cloud data"):
        # Clear the cloud data cache so the next load fetches fresh CSV, then reload the app
        try:
            from utils.load_data import load_cloud_data

            # Prefer clearing the specific loader cache if available
            if hasattr(load_cloud_data, "clear"):
                load_cloud_data.clear()
            else:
                # Fallback: clear all cached data if supported
                if hasattr(st, "cache_data") and hasattr(st.cache_data, "clear"):
                    try:
                        st.cache_data.clear()
                    except Exception as e:
                        logger.debug("st.cache_data.clear() raised: %s", e)

            # Try to programmatically rerun the app if Streamlit supports it;
            # older or non-standard builds may not expose experimental_rerun.
            if hasattr(st, "experimental_rerun"):
                try:
                    st.experimental_rerun()
                except Exception as e:
                    # If rerun fails, fall through to a user message below and log why
                    logger.debug("st.experimental_rerun() failed: %s", e)

            # If we cannot programmatically rerun, inform the user to refresh manually
            st.sidebar.success("Cloud data cache cleared. Please reload the page to fetch fresh data.")

        except (ImportError, RuntimeError, OSError, AttributeError) as e:
            logger.exception("Error clearing cloud cache: %s", e)
            # Surface the error message to the user to aid debugging
            st.sidebar.error(f"Failed to clear cloud data cache: {e}")

    # No return value: app is cloud-only and will directly call load_cloud_data()
    return None