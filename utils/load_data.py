import pandas as pd
import streamlit as st
import requests
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _get_api_config():
    api_url = st.secrets.get("API_URL", "https://stablecoin-api-636795230004.us-central1.run.app")
    api_key = st.secrets.get("API_KEY")
    
    if not api_key:
        st.error("API_KEY not found in secrets. Please configure .streamlit/secrets.toml")
        return None, None
    
    return api_url, api_key


@st.cache_data(ttl=3600)
def get_last_updated() -> str:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return "Unknown"
    
    try:
        headers = {"X-API-Key": api_key}
        resp = requests.get(f"{api_url}/dashboard/last-updated", headers=headers, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        timestamp = data.get("last_updated", "Unknown")
        
        st.session_state["cloud_last_modified"] = f"{timestamp} (updated every 24 hours)"
        
        return timestamp
    except Exception as e:
        logger.exception("Error fetching last updated: %s", e)
        return "Unknown"


@st.cache_data(ttl=3600)
def get_dashboard_summary(hours: int = 24) -> dict:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return {}
    
    try:
        headers = {"X-API-Key": api_key}
        params = {"hours": hours}
        resp = requests.get(f"{api_url}/dashboard/summary", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        summary = resp.json()
        
        return summary
    except Exception as e:
        logger.exception("Error fetching dashboard summary: %s", e)
        st.error(f"Failed to fetch summary: {e}")
        return {}


@st.cache_data(ttl=3600)
def get_top_wallets(top_n: int = 100, sort_by: str = 'risk', hours: int = 24) -> pd.DataFrame:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return pd.DataFrame()
    
    try:
        headers = {"X-API-Key": api_key}
        params = {"top_n": top_n, "sort_by": sort_by, "hours": hours}
        resp = requests.get(f"{api_url}/dashboard/top-wallets", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        df = pd.DataFrame(data["data"])
        
        return df
    except Exception as e:
        logger.exception("Error fetching top wallets: %s", e)
        st.error(f"Failed to fetch top wallets: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_timeseries_data(hours: int = 24) -> pd.DataFrame:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return pd.DataFrame()
    
    try:
        headers = {"X-API-Key": api_key}
        params = {"hours": hours}
        resp = requests.get(f"{api_url}/dashboard/timeseries", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        df = pd.DataFrame(data["data"])
        
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        return df
    except Exception as e:
        logger.exception("Error fetching timeseries: %s", e)
        st.error(f"Failed to fetch timeseries: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_token_volume(hours: int = 24) -> pd.DataFrame:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return pd.DataFrame()
    
    try:
        headers = {"X-API-Key": api_key}
        params = {"hours": hours}
        resp = requests.get(f"{api_url}/dashboard/token-volume", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        df = pd.DataFrame(data["data"])
        
        return df
    except Exception as e:
        logger.exception("Error fetching token volume: %s", e)
        st.error(f"Failed to fetch token volume: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_risk_distribution(tokens: list = None) -> pd.DataFrame:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return pd.DataFrame()
    
    try:
        headers = {"X-API-Key": api_key}
        params = {}
        if tokens:
            params["tokens"] = ",".join(tokens)
        
        resp = requests.get(f"{api_url}/dashboard/risk-distribution", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        df = pd.DataFrame(data["data"])
        
        return df
    except Exception as e:
        logger.exception("Error fetching risk distribution: %s", e)
        st.error(f"Failed to fetch risk distribution: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_component_scores(tokens: list = None) -> pd.DataFrame:
    api_url, api_key = _get_api_config()
    if not api_url or not api_key:
        return pd.DataFrame()
    
    try:
        headers = {"X-API-Key": api_key}
        params = {}
        if tokens:
            params["tokens"] = ",".join(tokens)
        
        resp = requests.get(f"{api_url}/dashboard/component-scores", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        df = pd.DataFrame(data["data"])
        
        return df
    except Exception as e:
        logger.exception("Error fetching component scores: %s", e)
        st.error(f"Failed to fetch component scores: {e}")
        return pd.DataFrame()
