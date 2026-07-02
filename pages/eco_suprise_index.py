import streamlit as st
import plotly.graph_objects as go
from analyzer import init_analyzer as get_analyzer
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


st.header("📈 Eco Surprise Index")
st.markdown(
    "Bullish percentage for each currency – the proportion of economic indicators that beat forecasts."
)
# Helper: compute bullish % using only CORE indicators (and currency-specific extras)
def compute_surprise_pct(curr):
    indicators = list(CORE_INDICATORS)
    if curr in EXTRA_INDICATORS:
        indicators.extend(EXTRA_INDICATORS[curr])
    data = analyzer.raw_data.get(curr, {})
    beats = 0
    surprises = 0
    for ind in indicators:
        if ind not in data:
            continue
        actual, forecast, _, _ = data[ind]
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
percentages = {
    curr: compute_surprise_pct(curr)
    for curr in STANDARD_CURRENCIES
    if curr in analyzer.raw_data
}
if not percentages:
    st.warning(
        "No currency fundamental data loaded yet. Please upload or update indicators."
    )
    st.stop()
cols_per_row = 4
currency_list = sorted(percentages.keys())
rows = [
    currency_list[i : i + cols_per_row]
    for i in range(0, len(currency_list), cols_per_row)
]
for row_currencies in rows:
    cols = st.columns(cols_per_row)
    for idx, currency in enumerate(row_currencies):
        with cols[idx]:
            bullish_pct = percentages[currency]
            if bullish_pct >= 60:
                color = "#00ff88"
            elif bullish_pct >= 40:
                color = "#ffaa00"
            else:
                color = "#ff4b4b"
            fig = go.Figure(
                go.Pie(
                    values=[bullish_pct, 100 - bullish_pct],
                    labels=["", ""],
                    hole=0.7,
                    marker=dict(colors=[color, "#1e2430"]),
                    textinfo="none",
                    hoverinfo="skip",
                    showlegend=False,
                    sort=False,
                    direction="clockwise",
                )
            )
            fig.add_annotation(
                text=f"<b>{bullish_pct:.0f}%</b>",
                x=0.5,
                y=0.5,
                font=dict(size=22, color="white"),
                showarrow=False,
            )
            fig.add_annotation(
                text=currency,
                x=0.5,
                y=-0.18,
                xref="paper",
                yref="paper",
                font=dict(size=14, color="#94a3b8"),
                showarrow=False,
            )
            fig.update_layout(
                height=240,
                margin=dict(l=10, r=10, t=20, b=40),
                paper_bgcolor="#0b0f15",
                plot_bgcolor="#0b0f15",
            )
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
