import pandas as pd
from pathlib import Path
from utils.public_scoring import compute_public_risk_scores
import streamlit as st
import requests
import io
import logging
import tempfile
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@st.cache_data(ttl=3600)
def load_cloud_data() -> pd.DataFrame:
    """Load pre-processed data from Google Cloud Storage public CSV.

    Uses `requests` for secure TLS handling and persists the `Last-Modified`
    timestamp to a small cache file under `.cache/` so it survives full page reloads.
    """
    cloud_url = "https://storage.googleapis.com/stablecoin-dashboard-public/real_scores.csv"
    cache_path = Path(__file__).parent.parent / ".cache" / "cloud_last_modified.txt"

    try:
        resp = requests.get(cloud_url, stream=True, timeout=30)
        resp.raise_for_status()

        last_modified = resp.headers.get("Last-Modified")
        if last_modified:
            try:
                from email.utils import parsedate_to_datetime

                last_update = parsedate_to_datetime(last_modified)
                # normalize to UTC string
                last_update = last_update.astimezone(timezone.utc)
                formatted = last_update.strftime("%Y-%m-%d %H:%M:%S UTC")
                st.session_state["cloud_last_modified"] = formatted

                # persist atomically to .cache
                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    # write to temp file then atomic replace
                    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(cache_path.parent)) as tf:
                        tf.write(formatted)
                        temp_name = tf.name
                    os.replace(temp_name, str(cache_path))
                except OSError as e:
                    logger.warning("Failed to write cloud_last_modified cache: %s", e)
            except (TypeError, ValueError, ImportError) as e:
                # These are the likely failures: malformed header, parsing errors,
                # or missing stdlib function (very unlikely). Log as a warning only.
                logger.warning("Failed to parse Last-Modified header: %s", e)

        # Read CSV from response content (safer for stream handling)
        content = resp.content
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))

        if df.empty:
            st.warning("No data returned from cloud storage.")
            return pd.DataFrame()

        # Normalize and compute scores
        df = compute_public_risk_scores(df)
        return df

    except requests.exceptions.RequestException as e:
        logger.exception("Error fetching cloud CSV: %s", e)
        st.error(f"Cloud storage fetch error: {e}")
        return pd.DataFrame()