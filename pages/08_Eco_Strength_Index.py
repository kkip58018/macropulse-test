import streamlit as st
import pandas as pd
from config import *
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

st.markdown(
    """
<style>
.title-container {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
}
.title-text {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
}
.info-icon-wrapper {
    position: relative;
    display: inline-block;
}
.info-icon {
    background-color: #1e2430;
    color: #94a3b8;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 14px;
    cursor: help;
    border: 1px solid #2a3340;
}
.info-tooltip {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    top: 30px;
    left: -20px;
    background-color: #0f131a;
    border: 1px solid #1e2430;
    border-radius: 8px;
    padding: 16px 20px;
    width: 480px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    z-index: 1000;
    transition: opacity 0.2s;
    color: #ddd;
    font-size: 13px;
    line-height: 1.6;
    pointer-events: none;
}
.info-icon-wrapper:hover .info-tooltip {
    visibility: visible;
    opacity: 1;
}
.tooltip-title {
    color: #00b8ff;
    font-weight: bold;
    margin-bottom: 8px;
}
</style>
<div class="title-container">
    <h1 class="title-text">🌍 EF Economic Strength Index</h1>
    <div class="info-icon-wrapper">
        <span class="info-icon">ℹ️</span>
        <div class="info-tooltip">
            <div class="tooltip-title">How the Economic Strength Index Works</div>
            <div>The Economic Strength Index ranks major currencies by relative economic health. It combines five key macroeconomic indicators into a single composite <b>Total Score</b> (0-100). Higher scores indicate greater strength.</div>
            <br>
            <div class="tooltip-title">Component Influence</div>
            <div><b>GDP Growth</b> – signals expansion, attracts investment → bullish.</div>
            <div><b>Unemployment Rate</b> – lower is better; robust labour market → bullish.</div>
            <div><b>Interest Rate</b> – higher rates attract yield‑seeking capital → bullish.</div>
            <div><b>CPI (inflation) YoY</b> – moderate inflation (≈2%) is ideal; extremes hurt.</div>
            <div><b>Real Yields</b> (nominal rate – inflation) – positive real yields reward holding → bullish.</div>
            <br>
            <div class="tooltip-title">Scoring</div>
            <div>Each component is normalised (0-100%) against typical ranges, then weighted:</div>
            <div>• GDP: 25%  • Unemployment: 20%  • Interest Rate: 25%  • CPI: 15%  • Real Yield: 15%</div>
            <br>
            <div><b>Bias</b>: ≥60 Bullish, 40-59 Neutral, ≤39 Bearish.</div>
            <div><b>Δ Score</b> & <b>Δ Real Yield</b> show change from previous update.</div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("Long‑term fundamental ranking indicator, based on latest data")
# Fetch data
analyzer._load_economic_strength()
data = getattr(analyzer, "economic_strength", {})
# Ensure all standard currencies appear
all_currencies = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"]
rows = []
for curr in all_currencies:
    d = data.get(curr, {})
    rows.append(
        {
            "Currency": curr,
            "Bias": d.get("bias", "Neutral"),
            "Relative Strength Score": d.get("relative_strength_score", 50),
            "Δ Score": d.get("delta_score", 0),
            "GDP Growth": f"{d.get('gdp_growth', 0):.2f}%",
            "Unemployment Rate": f"{d.get('unemployment_rate', 0):.2f}%",
            "Interest Rate": f"{d.get('interest_rate', 0):.2f}%",
            "CPI YoY": f"{d.get('cpi_yoy', 0):.2f}%",
            "Real Yield": f"{d.get('real_yield', 0):.2f}%",
            "Δ Real Yield": d.get("delta_real_yield", 0),
        }
    )
df = pd.DataFrame(rows)
df = df.sort_values("Relative Strength Score", ascending=False)
# Styling functions
def color_bias(val):
    if val == "Bullish":
        return "background-color: #1e3a2e; color: #00ff88; font-weight: bold"
    elif val == "Bearish":
        return "background-color: #3a1e1e; color: #ff4b4b; font-weight: bold"
    else:
        return "background-color: #3a3a1e; color: #ffaa00"
def color_score(val):
    try:
        v = int(val)
        if v >= 60:
            return "color: #00ff88; font-weight: bold"
        elif v <= 40:
            return "color: #ff4b4b; font-weight: bold"
    except:
        pass
    return ""
def color_delta(val):
    if val > 0:
        return "color: #00ff88"
    elif val < 0:
        return "color: #ff4b4b"
    return ""
styled = (
    df.style.map(color_bias, subset=["Bias"])
    .map(color_score, subset=["Relative Strength Score"])
    .map(color_delta, subset=["Δ Score", "Δ Real Yield"])
    .format({"Δ Score": "{:+d}", "Δ Real Yield": "{:+.2f}%"})
)
st.dataframe(styled, use_container_width=True, hide_index=True)
