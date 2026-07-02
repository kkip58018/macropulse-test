import streamlit as st
from analyzer import init_analyzer as get_analyzer

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = get_analyzer()


st.header("⚙️ Trend Detection Settings")
st.markdown(
    "Configure the moving average periods used for trend analysis from TradingView / Yahoo Finance."
)
if st.button("🔄 Refresh All Trend Data Now"):
    with st.spinner("Fetching latest trend data for all pairs..."):
        analyzer.refresh_all_trends()
    st.session_state.success_msg = (
        "Trend data refreshed successfully! Cached trend scores updated."
    )
    st.rerun()
current_periods = analyzer.ma_periods
st.write("**Current SMA periods:**", current_periods)
periods_input = st.text_input(
    "Enter SMA periods (comma-separated, e.g., 20,50,100,200)",
    value=",".join(str(p) for p in current_periods),
)
if st.button("Save Settings"):
    try:
        new_periods = [
            int(p.strip()) for p in periods_input.split(",") if p.strip()
        ]
        if new_periods:
            if analyzer.update_ma_periods(new_periods):
                st.session_state.success_msg = f"Trend SMA periods updated to {new_periods}. The trend cache has been cleared; click 'Refresh All Trend Data Now' to repopulate."
                st.rerun()
            else:
                st.error("Failed to save settings.")
        else:
            st.error("Please enter at least one valid period.")
    except ValueError:
        st.error("Invalid input. Please enter numbers separated by commas.")
st.info(
    "Trend scores are cached after first fetch. Use the refresh button above to update all trend data manually."
)
