import streamlit as st
from utils.generate_demo_data import generate_demo_data
from utils.convert_real_data import convert_raw_to_real_scores

def _sync_data_source():
    st.session_state["data_source"] = st.session_state["_data_source"]

def sidebar():
    # Ensure persistent state exists first
    if "data_source" not in st.session_state:
        st.session_state["data_source"] = "Demo Data"

    # Widget state always mirrors persistent state before rendering
    st.session_state["_data_source"] = st.session_state["data_source"]

    st.sidebar.subheader("Data source")
    st.sidebar.radio(
        "Choose dataset",
        ["Demo Data", "Real Data"],
        key="_data_source",
        on_change=_sync_data_source,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Data actions")

    if st.sidebar.button("🔁 Generate Demo Dataset"):
        generate_demo_data()
        st.session_state["data_source"] = "Demo Data"
        st.session_state["_data_source"] = "Demo Data"
        st.success("Demo dataset has been generated.")

    if st.sidebar.button("📂 Convert Real Data"):
        convert_raw_to_real_scores()
        st.session_state["data_source"] = "Real Data"
        st.session_state["_data_source"] = "Real Data"
        st.success("Real dataset has been converted and loaded.")

    # Always return the persistent value (now guaranteed to exist)
    return st.session_state["data_source"]