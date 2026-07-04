import streamlit as st
import pandas as pd
from sidebar import render as render_sidebar
from analyzer import init_analyzer

# ---------- Authentication guard ----------
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")
    

# ---------- Render the custom sidebar ----------
render_sidebar()

# ---------- Get the analyzer ----------
analyzer = init_analyzer()  # cached

# ---------- Page content (copy from original) ----------         
st.header("🏆 Top Setups")
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input(
        "Search Asset", key="top_setups_search", placeholder="e.g., EUR, XAU, USD"
    )
with col2:
    filter_type = st.selectbox(
        "Filter", ["All", "Bullish Only", "Bearish Only", "Exclude Neutral"]
    )
# Get pairs and currencies
enriched_items = analyzer.get_enriched_pairs(include_currencies=True)
if filter_type == "Bullish Only":
    enriched_items = [p for p in enriched_items if p[3] is not None and p[3] >= 5]
elif filter_type == "Bearish Only":
    enriched_items = [p for p in enriched_items if p[3] is not None and p[3] <= -5]
elif filter_type == "Exclude Neutral":
    enriched_items = [
        p for p in enriched_items if p[3] is not None and (p[3] <= -5 or p[3] >= 5)
    ]
# Apply search filter (case-insensitive)
if search_term:
    search_lower = search_term.strip().lower()
    enriched_items = [
        p
        for p in enriched_items
        if search_lower in (f"{p[0]}/{p[1]}" if p[1] else p[0]).lower()
    ]
if not enriched_items:
    st.warning("No items match the selected filter or search term.")
    st.stop()
enriched_items.sort(key=lambda x: x[3] if x[3] is not None else -999, reverse=True)
df_data = []
for base, quote, bias, overall, fund, cot, retail, trend, season in enriched_items:
    def fmt_int(val):
        if val is None:
            return "N/A"
        try:
            return int(val)
        except:
            return val
    # For currencies, quote is empty; display as just the currency code
    display_name = f"{base}" if not quote else f"{base}/{quote}"
    df_data.append(
        {
            "Asset": display_name,
            "Bias": bias if bias else "N/A",
            "Overall Score": fmt_int(overall),
            "Fundamentals": fmt_int(fund),
            "COT": fmt_int(cot),
            "Contrarian Retail": fmt_int(retail),
            "Trend": fmt_int(trend),
            "Seasonality": fmt_int(season),
        }
    )
df = pd.DataFrame(df_data)
def style_bias(val):
    if "Bullish" in str(val):
        return "background-color: #1e3a2e; color: #00ff88; font-weight: bold"
    if "Bearish" in str(val):
        return "background-color: #3a1e1e; color: #ff4b4b; font-weight: bold"
    if "Neutral" in str(val):
        return "background-color: #3a3a1e; color: #ffaa00"
    return ""
def style_overall(val):
    if val == "N/A":
        return ""
    try:
        v = int(val)
        if v >= 5:
            return "background-color: #1e3a2e; color: #00ff88"
        if v <= -5:
            return "background-color: #3a1e1e; color: #ff4b4b"
        return "background-color: #2a2a2a; color: #ffaa00"
    except:
        return ""
if not df.empty and "Bias" in df.columns and "Overall Score" in df.columns:
    styled_df = df.style.map(style_bias, subset=["Bias"]).map(
        style_overall, subset=["Overall Score"]
    )
    st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)
else:
    st.dataframe(df, use_container_width=True, height=600, hide_index=True)

