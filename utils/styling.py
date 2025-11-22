"""Styling utilities for icons and custom CSS."""
import streamlit as st


def inject_icon_styles():
    """Inject Material Icons and Font Awesome CSS for better tab icons."""
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 16px;
        }
        .stTabs [data-baseweb="tab-list"] button i {
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
