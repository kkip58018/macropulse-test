# sidebar.py
import streamlit as st
from config import *
from db import supabase_auth
import time

# ---------- Mapping from page script name to display name ----------
PAGE_DISPLAY_MAP = {
    "1_Dashboard": "🏆 Top Setups",
    "2_Asset_Scorecard": "📋 Asset Scorecard",
    "3_Forex_Scorecard": "📊 Forex Scorecard",
    "4_COT_Report": "📉 Latest COT Report",
    "5_COT_Trends": "📈 COT Trends",
    "6_COT_History": "📊 COT Data history",
    "7_Eco_Surprise": "📈 Eco surprise index",
    "8_Economic_Strength": "🌍 Economic Strength Index",
    "9_Monthly_Seasonality": "📅 Monthly Seasonality",
    "10_Annual_Seasonality": "📈 Annual Seasonality",
    "11_Retail_Sentiment": "🔄 Retail Sentiment",
    "12_Put_Call_Ratio": "📊Put-Call Ratio",
    "13_Economic_Heatmap": "🔥 Economic Heatmap",
    "14_Economic_Calendar": "📅 Economic calendar",
    "15_Reload_Data": "🔄 Reload Data",
    "16_Data_Updates": "✏️ Data Updates",
    "17_Trend_Settings": "⚙️ Trend Settings",
    "18_User_Approvals": "👥 User Approvals",
}
DISPLAY_TO_SCRIPT = {v: k for k, v in PAGE_DISPLAY_MAP.items()}

# ---------- Navigation groups (exactly as in original) ----------
nav_main_top = ["🏆 Top Setups", "📋 Asset Scorecard", "📊 Forex Scorecard"]
nav_cot_data = ["📉 Latest COT Report", "📈 COT Trends", "📊 COT Data history"]
nav_macro_scanners = ["📈 Eco surprise index", "🌍 Economic Strength Index"]
nav_seasonality_scanners = ["📅 Monthly Seasonality", "📈 Annual Seasonality"]
nav_crowd_sentiment = ["🔄 Retail Sentiment", "📊Put-Call Ratio"]
nav_main_bottom = ["🔥 Economic Heatmap", "📅 Economic calendar", "🔄 Reload Data"]
nav_options_admin = ["✏️ Data Updates", "⚙️ Trend Settings", "👥 User Approvals"]

# ---------- Helper: get index of active page in a list ----------
def get_index(page_list):
    active_display = st.session_state.get("_active_display", "")
    if active_display in page_list:
        return page_list.index(active_display)
    return None

# ---------- The sidebar renderer ----------
def render():
    # 1. Determine active page from the current script path
    page_script = st.page_info["page_script"].stem
    active_display = PAGE_DISPLAY_MAP.get(page_script, "")
    st.session_state["_active_display"] = active_display

    # 2. CSS to hide the default sidebar nav
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 3. Sidebar header with custom toggle (if you want)
    # We'll just show the navigation heading
    st.sidebar.markdown("## Navigation")

    # 4. Top main options (no expander)
    selected = st.sidebar.radio(
        "nav_top",
        nav_main_top,
        index=get_index(nav_main_top),
        label_visibility="collapsed",
        key="nav_top",
    )
    if selected != active_display and selected in DISPLAY_TO_SCRIPT:
        st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
        st.stop()

    # 5. COT Data expander
    with st.sidebar.expander("👥 COT Data", expanded=active_display in nav_cot_data):
        selected = st.radio(
            "nav_cot",
            nav_cot_data,
            index=get_index(nav_cot_data),
            label_visibility="collapsed",
            key="nav_cot",
        )
        if selected != active_display and selected in DISPLAY_TO_SCRIPT:
            st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
            st.stop()

    # 6. Macro Scanners expander
    with st.sidebar.expander("🔎 Macro Scanners", expanded=active_display in nav_macro_scanners):
        selected = st.radio(
            "nav_macro",
            nav_macro_scanners,
            index=get_index(nav_macro_scanners),
            label_visibility="collapsed",
            key="nav_macro",
        )
        if selected != active_display and selected in DISPLAY_TO_SCRIPT:
            st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
            st.stop()

    # 7. Seasonality Scanners expander
    with st.sidebar.expander("🍂 Seasonality Scanners", expanded=active_display in nav_seasonality_scanners):
        selected = st.radio(
            "nav_season",
            nav_seasonality_scanners,
            index=get_index(nav_seasonality_scanners),
            label_visibility="collapsed",
            key="nav_season",
        )
        if selected != active_display and selected in DISPLAY_TO_SCRIPT:
            st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
            st.stop()

    # 8. Crowd Sentiment expander
    with st.sidebar.expander("👥 Crowd Sentiment", expanded=active_display in nav_crowd_sentiment):
        selected = st.radio(
            "nav_crowd",
            nav_crowd_sentiment,
            index=get_index(nav_crowd_sentiment),
            label_visibility="collapsed",
            key="nav_crowd",
        )
        if selected != active_display and selected in DISPLAY_TO_SCRIPT:
            st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
            st.stop()

    # 9. Bottom main options (no expander)
    selected = st.sidebar.radio(
        "nav_bottom",
        nav_main_bottom,
        index=get_index(nav_main_bottom),
        label_visibility="collapsed",
        key="nav_bottom",
    )
    if selected != active_display and selected in DISPLAY_TO_SCRIPT:
        st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
        st.stop()

    # 10. Admin options (if admin)
    if st.session_state.get("is_admin", False):
        selected = st.sidebar.radio(
            "nav_admin",
            nav_options_admin,
            index=get_index(nav_options_admin),
            label_visibility="collapsed",
            key="nav_admin",
        )
        if selected != active_display and selected in DISPLAY_TO_SCRIPT:
            st.switch_page(f"pages/{DISPLAY_TO_SCRIPT[selected]}.py")
            st.stop()

    st.sidebar.markdown("---")

    # 11. User info and logout
    if st.session_state.get("user_email"):
        user_name = st.session_state.user_email.split("@")[0]
        st.sidebar.markdown(f"Hello, **{user_name}**")
    if st.sidebar.button("Logout"):
        try:
            supabase_auth.auth.sign_out()
        except:
            pass
        # Clear session
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.user_email = None
        st.rerun()
