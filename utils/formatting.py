import streamlit as st
import pandas as pd

def format_volume(value: float) -> str:
	if value >= 1_000_000_000:
		return f"${value/1_000_000_000:.2f}B"
	elif value >= 1_000_000:
		return f"${value/1_000_000:.2f}M"
	elif value >= 1_000:
		return f"${value/1_000:.2f}K"
	else:
		return f"${value:.2f}"
