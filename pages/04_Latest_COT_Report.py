import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from analyzer import init_analyzer as get_analyzer
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


# Get the latest COT date from the database
latest_db_date = "N/A"
if analyzer.cot_raw:
    dates = [
        item.get("latest_date")
        for item in analyzer.cot_raw
        if item.get("latest_date")
    ]
    if dates:
        latest_db_date = max(dates)
# Title row with date on the far right
title_col, date_col = st.columns([3, 1])
with title_col:
    st.header("📉 COT (Commitment of Traders)")
with date_col:
    st.markdown(
        f"<p style='text-align: right; margin-top: 1.2rem;'><strong>📅 last updated:</strong> {latest_db_date}</p>",
        unsafe_allow_html=True,
    )
# Admin‑only refresh button
if st.session_state.get("is_admin", False):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Refresh COT data**")
    with col2:
        if st.button("🔄 Refresh COT", use_container_width=True):
            with st.spinner("Getting COT data..."):
                progress_bar = st.progress(0, text="Updating COT records...")
                def update_progress(current, total):
                    progress_bar.progress(
                        current / total, text=f"Updating {current}/{total}"
                    )
                updated = analyzer.refresh_cot_data_from_web(update_progress)
                progress_bar.empty()
            if updated > 0:
                st.session_state.success_msg = (
                    f"COT data refreshed from web. Updated {updated} records."
                )
                st.rerun()
            else:
                st.error(
                    "Failed to refresh COT data. Check the console or try manual entry."
                )
if analyzer.cot_current:
    # ----- STACKED BAR CHART -----
    st.subheader("Current Net Positions")
    assets = list(analyzer.cot_current.keys())
    sorted_assets = sorted(assets, key=lambda a: analyzer.cot_current[a])
    long_vals = [analyzer.cot_current[a] for a in sorted_assets]
    short_vals = [100.0 - v for v in long_vals]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=sorted_assets,
            y=long_vals,
            name="Long",
            marker_color="#1e3a5f",
            hovertemplate="%{y:.1f}% Long<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sorted_assets,
            y=short_vals,
            name="Short",
            marker_color="#5f1e1e",
            hovertemplate="%{y:.1f}% Short<extra></extra>",
        )
    )
    fig.update_layout(
        barmode="stack",
        yaxis=dict(
            range=[0, 100],
            ticksuffix="%",
            gridcolor="rgba(128,128,128,0.2)",
            title="",
        ),
        xaxis=dict(title="", tickangle=0),
        template="plotly_dark",
        paper_bgcolor="#0b0f15",
        plot_bgcolor="#0b0f15",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        height=450,
    )
    st.plotly_chart(
        fig, use_container_width=True, config={"displayModeBar": False}
        )
    # ----- ASSETS TABLE (detailed raw data, no open interest) -----
    st.subheader("Latest buys and sells - Assets")
    if analyzer.cot_raw:
        asset_table = []
        for item in analyzer.cot_raw:
            sym = item["asset"]
            cur_long = item["latest_long"]
            cur_short = item["latest_short"]
            cur_long_pct = item["latest_long_pct"]
            cur_short_pct = 100.0 - cur_long_pct
            cur_net_pct = cur_long_pct - cur_short_pct
            prev_long = item.get("prev_long", cur_long)
            prev_short = item.get("prev_short", cur_short)
            delta_long = cur_long - prev_long
            delta_short = cur_short - prev_short
            prev_long_pct = item.get("prev_long_pct", cur_long_pct)
            prev_short_pct = 100.0 - prev_long_pct
            prev_net_pct = prev_long_pct - prev_short_pct
            net_pct_change = cur_net_pct - prev_net_pct
            if cur_net_pct >= 20:
                position = "Bullish"
            elif cur_net_pct <= -20:
                position = "Bearish"
            else:
                position = "Neutral"
            asset_table.append(
                {
                    "Symbol": sym,
                    "Long Contracts": cur_long,
                    "Short Contracts": cur_short,
                    "Δ Long": delta_long,
                    "Δ Short": delta_short,
                    "Long %": cur_long_pct,
                    "Short %": cur_short_pct,
                    "Net % Change": net_pct_change,
                    "Net Position": position,
                }
            )
        df_assets = pd.DataFrame(asset_table)
        df_assets = df_assets.sort_values("Net % Change", ascending=False)
        def color_delta(val):
            try:
                num = float(val)
                return f"color: {'#00ff88' if num >= 0 else '#ff4b4b'}; font-weight: bold"
            except:
                return ""
        def color_position(val):
            if val == "Bullish":
                return (
                    "background-color: #1e3a5f; color: #00b8ff; font-weight: bold"
                )
            elif val == "Bearish":
                return (
                    "background-color: #5f1e1e; color: #ff4b4b; font-weight: bold"
                )
            else:
                return "background-color: #2a2a2a; color: #ccc; font-weight: bold"
        styled_assets = (
            df_assets.style.map(
                color_delta, subset=["Δ Long", "Δ Short", "Net % Change"]
            )
            .map(color_position, subset=["Net Position"])
            .format(
                {
                    "Long Contracts": "{:.0f}",
                    "Short Contracts": "{:.0f}",
                    "Δ Long": "{:+.0f}",
                    "Δ Short": "{:+.0f}",
                    "Long %": "{:.1f}%",
                    "Short %": "{:.1f}%",
                    "Net % Change": "{:+.1f}%",
                }
            )
        )
        st.dataframe(styled_assets, use_container_width=True, hide_index=True)
    else:
        st.info("No COT raw data available. Insert records to populate the table.")
    # ----- PAIRS TABLE -----
    st.subheader("Pairs")
    net_cur = {
        c: analyzer.get_net_position(analyzer.cot_current[c])
        for c in analyzer.cot_current
    }
    net_prev = {
        c: analyzer.get_net_position(analyzer.cot_prev[c])
        for c in analyzer.cot_prev
    }
    change_data = []
    for pair_str in FOREX_PAIRS:
        base, quote = pair_str.split("/")
        if base not in net_cur or quote not in net_cur:
            continue
        net_diff = net_cur[base] - net_cur[quote]
        prev_diff = net_prev.get(base, 0) - net_prev.get(quote, 0)
        change = net_diff - prev_diff
        sentiment = (
            "Bullish"
            if change > 0.1
            else ("Bearish" if change < -0.1 else "Neutral")
        )
        net_pos = (
            "Bullish"
            if net_diff >= 20
            else ("Bearish" if net_diff <= -20 else "Neutral")
        )
        change_data.append(
            {
                "Pair": pair_str,
                "Net Change": change,
                "Sentiment": sentiment,
                "Net-Positioning": net_pos,
            }
        )
    change_data.sort(key=lambda x: x["Net Change"], reverse=True)
    if change_data:
        df_change = pd.DataFrame(change_data)
        def color_net_change(val):
            try:
                num = float(val)
                return f"color: {'#00ff88' if num >= 0 else '#ff4b4b'}; font-weight: bold"
            except:
                return ""
        styled_change = (
            df_change.style.map(color_net_change, subset=["Net Change"])
            .map(color_position, subset=["Sentiment", "Net-Positioning"])
            .format({"Net Change": "{:+.1f}"})
        )
        st.dataframe(styled_change, use_container_width=True, hide_index=True)
    else:
        st.info("No COT pair change data available.")
else:
    st.warning(
        "No COT data loaded. Please update COT via Data Updates menu or use the Refresh button above."
    )
