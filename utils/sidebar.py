import streamlit as st
from utils.generate_demo_data import generate_demo_data
from utils.convert_real_data import convert_raw_to_real_scores
from utils.load_data import load_demo_data, load_real_data

def sidebar():
    ss = st.session_state

    # Persistent app state
    if "data_source" not in ss:
        ss["data_source"] = "Real Data"

    with st.sidebar.expander("Settings", expanded=False):
        options = ["Demo Data", "Real Data"]
        current_index = options.index(ss["data_source"]) if ss["data_source"] in options else 1
        selected = st.radio(
            "Select data source",
            options,
            index=current_index,
            key="_data_source",
        )
        if selected != ss["data_source"]:
            ss["data_source"] = selected

        # Seed input bar
        seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=10_000_000,
            step=1,
            value=ss.get("seed", 42),
            key="seed",
        )

        # Demo dataset generator
        if st.button("Generate Demo Dataset"):
            generate_demo_data(seed=seed)
            load_demo_data.clear()
            ss["data_source"] = "Demo Data"
            st.success("Demo dataset has been generated.")

        # Real dataset converter
        if st.button("Convert Real Data"):
            convert_raw_to_real_scores()
            load_real_data.clear()
            ss["data_source"] = "Real Data"
            st.success("Real dataset has been converted and loaded.")

    # Return the persistent value
    return ss["data_source"]