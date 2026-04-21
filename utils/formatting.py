import streamlit as st
import pandas as pd

from datetime import datetime, timezone
from typing import Any, Optional

def format_volume(value: float) -> str:
	"""Format volume with abbreviated units (for metrics/cards)."""
	if value >= 1_000_000_000:
		return f"${value/1_000_000_000:.1f}B"
	elif value >= 1_000_000:
		return f"${value/1_000_000:.2f}M"
	elif value >= 1_000:
		return f"${value/1_000:.2f}K"
	else:
		return f"${value:.2f}"

def format_volume_exact(value: float) -> str:
	"""Format volume with exact comma-separated values (for tables)."""
	return f"${value:,.2f}"


def _to_datetime_utc(value: Any) -> Optional[datetime]:
	if value is None:
		return None
	if isinstance(value, datetime):
		dt = value
	elif isinstance(value, (int, float)):
		# Heuristic: treat very large values as milliseconds.
		ts = float(value)
		if ts > 1e12:
			ts = ts / 1000.0
		dt = datetime.fromtimestamp(ts, tz=timezone.utc)
	else:
		s = str(value).strip()
		if not s:
			return None
		# Handle common UTC suffix.
		if s.endswith("Z"):
			s = s[:-1] + "+00:00"
		try:
			dt = datetime.fromisoformat(s)
		except ValueError:
			# Best-effort parsing for common timestamp strings.
			for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
				try:
					dt = datetime.strptime(s, fmt)
					break
				except ValueError:
					dt = None
			if dt is None:
				return None

	if dt.tzinfo is None:
		# Assume UTC if no timezone info is present.
		dt = dt.replace(tzinfo=timezone.utc)
	return dt.astimezone(timezone.utc)


def format_relative_time(value: Any, now: Optional[datetime] = None, fallback: str = "Unknown") -> str:
	"""Return human-friendly relative time like '1 hour ago' for a timestamp-like input."""
	dt = _to_datetime_utc(value)
	if dt is None:
		return fallback if fallback is not None else str(value)

	ref = now.astimezone(timezone.utc) if isinstance(now, datetime) else datetime.now(timezone.utc)
	delta_seconds = (ref - dt).total_seconds()
	future = delta_seconds < 0
	seconds = abs(int(delta_seconds))

	if seconds < 10:
		return "just now" if not future else "in a few seconds"
	if seconds < 60:
		n = seconds
		unit = "second" if n == 1 else "seconds"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	minutes = seconds // 60
	if minutes < 60:
		n = minutes
		unit = "minute" if n == 1 else "minutes"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	hours = minutes // 60
	if hours < 24:
		n = hours
		unit = "hour" if n == 1 else "hours"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	days = hours // 24
	if days < 7:
		n = days
		unit = "day" if n == 1 else "days"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	weeks = days // 7
	if weeks < 5:
		n = weeks
		unit = "week" if n == 1 else "weeks"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	months = days // 30
	if months < 12:
		n = months
		unit = "month" if n == 1 else "months"
		return f"{n} {unit} ago" if not future else f"in {n} {unit}"

	years = days // 365
	n = years
	unit = "year" if n == 1 else "years"
	return f"{n} {unit} ago" if not future else f"in {n} {unit}"


def format_utc_timestamp(value: Any, fallback: str = "Unknown") -> str:
	"""Return an explicit UTC timestamp string like '2026-02-02 15:04:05 UTC'."""
	dt = _to_datetime_utc(value)
	if dt is None:
		return fallback if fallback is not None else str(value)
	return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def utc_now_timestamp() -> str:
	"""Current time in UTC formatted for display."""
	return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
