import streamlit as st
from analyzer import init_analyzer 
from config import *
from sidebar import render as render_sidebar

# ---------- Authentication guard ----------
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.stop()

# ---------- Render the custom sidebar ----------
render_sidebar()

# ---------- Get the analyzer ----------
analyzer = init_analyzer()  # cached

# ---------- Page content (copy from original) ----------

# Arrange title, refresh button (admin only), and filter in one row
if st.session_state.get("is_admin", False):
    col_title, col_btn, col_filter = st.columns([1, 0.6, 0.6])
    with col_title:
        st.header("🔄 Retail Sentiment")
    with col_btn:
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Fetching latest retail sentiment..."):
                analyzer._refresh_retail_sentiment_from_api(show_message=True)
            st.session_state.success_msg = "Retail sentiment updated."
            st.rerun()
    with col_filter:
        asset_filter = st.selectbox(
            "Filter",
            ["All", "Forex", "Crypto", "Metals", "Indices"],
            key="crowd_filter",
            label_visibility="collapsed",
        )
else:
    col_title, col_filter = st.columns([1, 0.6])
    with col_title:
        st.header("🔄 Retail Sentiment")
    with col_filter:
        asset_filter = st.selectbox(
            "Filter",
            ["All", "Forex", "Crypto", "Metals", "Indices"],
            key="crowd_filter",
            label_visibility="collapsed",
        )
# Gather all pairs that have retail data
all_pairs = set(FOREX_PAIRS)
all_pairs.add("ETH/USD")
if hasattr(analyzer, "retail_long_pct") and analyzer.retail_long_pct:
    valid_keys = {
        k
        for k in analyzer.retail_long_pct.keys()
        if k in FOREX_PAIRS or k == "ETH/USD"
    }
    all_pairs.update(valid_keys)
# Classify pairs
crypto_pairs = {"BTC/USD", "ETH/USD"}
metal_pairs = {"XAU/USD", "XAG/USD"}
index_pairs = {"SPX500/USD", "NAS100/USD"}
filtered_pairs = set()
for pair in all_pairs:
    if asset_filter == "All":
        filtered_pairs.add(pair)
    elif asset_filter == "Forex" and pair in FOREX_PAIRS:
        filtered_pairs.add(pair)
    elif asset_filter == "Crypto" and pair in crypto_pairs:
        filtered_pairs.add(pair)
    elif asset_filter == "Metals" and pair in metal_pairs:
        filtered_pairs.add(pair)
    elif asset_filter == "Indices" and pair in index_pairs:
        filtered_pairs.add(pair)
pairs_sorted = sorted(filtered_pairs)
if not pairs_sorted:
    st.info(
        "No retail sentiment data available. Check API connection or ask an admin to refresh."
    )
else:
    for pair in pairs_sorted:
        long_pct = analyzer.retail_long_pct.get(pair, 50.0)
        short_pct = 100.0 - long_pct
        score = analyzer.retail_scores.get(pair, 0)
        st.markdown(
            f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <div style="width: 100px; font-weight: bold; color: #ddd;">{pair}</div>
            <div style="flex: 1; display: flex; height: 24px; background-color: #1e2430; border-radius: 4px; overflow: hidden;">
                <div style="width: {long_pct}%; background-color: #1e3a5f; display: flex; align-items: center; padding-left: 6px;">
                    <span style="color: #e0e0e0; font-weight: bold; font-size: 0.85rem;">{long_pct:.1f}%</span>
                </div>
                <div style="width: {short_pct}%; background-color: #5f1e1e; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px;">
                    <span style="color: #e0e0e0; font-weight: bold; font-size: 0.85rem;">{short_pct:.1f}%</span>
                </div>
            </div>
            <div style="width: 40px; text-align: right; font-weight: bold; color: #ddd;">{score:+.0f}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
