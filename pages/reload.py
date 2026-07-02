import streamlit as st
from analyzer import init_analyzer 
import time

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = init_analyzer()

if st.button("Force Reload All Data"):
    with st.spinner("Reloading all data from database..."):
        analyzer.load_data()
        analyzer.trend_cache.clear()
        time.sleep(1)  # optional extra smoothness
    st.session_state.success_msg = "All data reloaded successfully"
    st.rerun()