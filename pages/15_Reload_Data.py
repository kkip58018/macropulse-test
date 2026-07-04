import streamlit as st
from analyzer import init_analyzer 
import time
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
if st.button("Force Reload All Data"):
    with st.spinner("Reloading all data from database..."):
        analyzer.load_data()
        analyzer.trend_cache.clear()
        time.sleep(1)  # optional extra smoothness
    st.session_state.success_msg = "All data reloaded successfully"
    st.rerun()
