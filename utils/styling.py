import streamlit as st


def inject_icon_styles():
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 16px;
        }
        .stTabs [data-baseweb="tab-list"] button i {
            margin-right: 8px;
        }

        /* Avoid ellipsis truncation in dataframes (e.g., full wallet addresses) */
        div[data-testid="stDataFrame"] div[role="gridcell"],
        .stDataFrame div[role="gridcell"] {
            white-space: normal !important;
            text-overflow: clip !important;
            overflow: visible !important;
            word-break: break-all !important;
        }
    </style>
    """, unsafe_allow_html=True)
