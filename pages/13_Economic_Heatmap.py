import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import *
from utils import format_date_dd_mon

from sidebar import render as render_sidebar
from analyzer import init_analyzer

# ---------- Authentication guard ----------
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.stop()

# ---------- Render the custom sidebar ----------
render_sidebar()

# ---------- Get the analyzer ----------
analyzer = init_analyzer()  # cached

# ---------- Page content (copy from original) ----------

st.header("🔥 Economic Heatmap")
# Row with economic indicator selector and refresh button (admin only)
if st.session_state.get("is_admin", False):
    col_curr, col_btn = st.columns([2, 1])
    with col_curr:
        currency = st.selectbox(
            "Select Currency", STANDARD_CURRENCIES, key="heatmap_currency"
        )
    with col_btn:
        if st.button(
            "🔄 Refresh from Web",
            use_container_width=True,
            help="Fetch latest economic data from Trading Economics / Investing.com",
        ):
            with st.spinner(f"Fetching indicators for {currency}..."):
                progress_text = st.empty()
                def update_progress(current, total):
                    progress_text.text(f"Progress: {current}/{total} indicators")
                updated, msg = analyzer.refresh_currency_indicators(
                    currency, update_progress
                )
                progress_text.empty()
                st.session_state.success_msg = (
                    f"✅ Web refresh completed for {currency}.\n{msg}"
                )
                st.rerun()
else:
    # Non‑admin: only the currency selector (full width)
    currency = st.selectbox(
        "Select Currency", STANDARD_CURRENCIES, key="heatmap_currency"
    )
if currency in analyzer.raw_data:
    data = analyzer.raw_data[currency]
    indicators = list(CORE_INDICATORS)
    if currency in EXTRA_INDICATORS:
        indicators.extend(EXTRA_INDICATORS[currency])
    rows = []
    for ind in indicators:
        if ind not in data:
            continue
        actual, forecast, date_val, prev_val = data[ind]
        direction = DIRECTION.get(ind)
        if not direction:
            continue
        surprise = (
            actual - forecast
            if actual is not None and forecast is not None
            else None
        )
        rows.append(
            {
                "Indicator": ind,
                "Date": format_date_dd_mon(date_val),
                "Previous": (
                    f"{prev_val:.2f}"
                    if isinstance(prev_val, float)
                    else str(prev_val) if prev_val else "N/A"
                ),
                "Forecast": f"{forecast:.2f}" if forecast is not None else "N/A",
                "Actual": f"{actual:.2f}" if actual is not None else "N/A",
                "Surprise": f"{surprise:+.2f}" if surprise is not None else "N/A",
            }
        )
    df = pd.DataFrame(rows)
    table_height = len(df) * 30 + 38
    st.dataframe(df, use_container_width=True, hide_index=True, height=table_height)
    # Bullish percentage (unchanged)
    def compute_surprise_pct(curr):
        ind_list = list(CORE_INDICATORS)
        if curr in EXTRA_INDICATORS:
            ind_list.extend(EXTRA_INDICATORS[curr])
        d = analyzer.raw_data.get(curr, {})
        beats = 0
        surprises = 0
        for ind in ind_list:
            if ind not in d:
                continue
            actual, forecast, _, _ = d[ind]
            if actual is None or forecast is None or actual == forecast:
                continue
            direction = DIRECTION.get(ind)
            if direction is None:
                continue
            surprises += 1
            if (direction == "higher" and actual > forecast) or (
                direction == "lower" and actual < forecast
            ):
                beats += 1
        return (beats / surprises * 100.0) if surprises > 0 else 0.0
    bullish = compute_surprise_pct(currency)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=bullish,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Bullish %"},
            gauge={
                "axis": {
                    "range": [None, 100],
                    "tickwidth": 1,
                    "tickcolor": "white",
                },
                "bar": {
                    "color": (
                        "#00ff88"
                        if bullish > 60
                        else "#ffaa00" if bullish > 40 else "#ff4b4b"
                    )
                },
                "bgcolor": "#1e2430",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#3a1e1e"},
                    {"range": [40, 60], "color": "#3a3a1e"},
                    {"range": [60, 100], "color": "#1e3a2e"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.75,
                    "value": 60,
                },
            },
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#0b0f15",
        font=dict(color="white"),
    )
    _, col_gauge = st.columns([2, 1])
    with col_gauge:
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
            )
else:
    st.warning(
        "Currency data not loaded yet. Please add some data via Updates menu or use the Refresh button above."
    )
