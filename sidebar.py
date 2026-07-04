# sidebar.py
import streamlit as st
import re
from pathlib import Path
import inspect
from config import *
from db import supabase_auth

# ---------- Mapping from page script name to display name ----------
PAGE_DISPLAY_MAP = {
    "01_Top_Setups": "🏆 Top Setups",
    "02_Asset_Scorecard": "📋 Asset Scorecard",
    "03_Forex_Scorecard": "📊 Forex Scorecard",
    "04_LatestCOT_Report": "📉 Latest COT Report",
    "05_COT_Trends": "📈 COT Trends",
    "06_COT_Data_History": "📊 COT Data history",
    "07_Eco_Suprise_index": "📈 Eco surprise index",
    "08_Economic_Strength_index": "🌍 Economic Strength Index",
    "09_Monthly_Seasonality": "📅 Monthly Seasonality",
    "10_Annual_Seasonality": "📈 Annual Seasonality",
    "11_Retail_Sentiment": "🔄 Retail Sentiment",
    "12_Put-Call_Ratio": "📊Put-Call Ratio",
    "13_Economic_Heatmap": "🔥 Economic Heatmap",
    "14_Economic_Calendar": "📅 Economic calendar",
    "15_Reload_Data": "🔄 Reload Data",
    "Data_Updates": "✏️ Data Updates",
    "Trend_Settings": "⚙️ Trend Settings",
    "User_Approvals": "👥 User Approvals",
}

def _normalize_key(key):
    return re.sub(r'^[0-9_]+', '', key).replace('_', '').lower()

DISPLAY_TO_SCRIPT = {v: k for k, v in PAGE_DISPLAY_MAP.items()}
NORMALIZED_TO_DISPLAY = {}
for script, display in PAGE_DISPLAY_MAP.items():
    norm = _normalize_key(script)
    NORMALIZED_TO_DISPLAY[norm] = display

# ---------- Navigation groups ----------
nav_main_top = ["🏆 Top Setups", "📋 Asset Scorecard", "📊 Forex Scorecard"]
nav_cot_data = ["📉 Latest COT Report", "📈 COT Trends", "📊 COT Data history"]
nav_macro_scanners = ["📈 Eco surprise index", "🌍 Economic Strength Index"]
nav_seasonality_scanners = ["📅 Monthly Seasonality", "📈 Annual Seasonality"]
nav_crowd_sentiment = ["🔄 Retail Sentiment", "📊Put-Call Ratio"]
nav_main_bottom = ["🔥 Economic Heatmap", "📅 Economic calendar", "🔄 Reload Data"]
nav_options_admin = ["✏️ Data Updates", "⚙️ Trend Settings", "👥 User Approvals"]

def get_index(page_list):
    active_display = st.session_state.get("_active_display", "")
    if active_display in page_list:
        return page_list.index(active_display)
    return None

def render():
    # --- Determine active page ---
    try:
        frame = inspect.currentframe().f_back
        caller_file = frame.f_globals['__file__']
        page_script = Path(caller_file).stem
    except Exception:
        page_script = ""

    norm = _normalize_key(page_script)
    active_display = NORMALIZED_TO_DISPLAY.get(norm, "")
    st.session_state["_active_display"] = active_display

    # --- Custom sidebar styling (radio buttons, expanders) ---
    st.markdown(
        """
        <style>
        /* Hide native radio circles */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {
            display: none !important;
        }

        /* Reset label container */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            padding: 0 !important;
            margin: 0 0 2px 0 !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Style the text wrapper */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input + div {
            padding: 0.6rem 1rem !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            cursor: pointer !important;
            width: 100% !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }

        /* Inactive text color */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input + div p {
            color: #94a3b8 !important;
            margin: 0 !important;
        }

        /* Hover state for inactive items */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:not(:checked) + div:hover {
            background-color: rgba(255, 255, 255, 0.05) !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:not(:checked) + div:hover p {
            color: #ffffff !important;
        }

        /* Active / selected state – grey background as in original */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div {
            background-color: #374151 !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Remove extra spacing between radio items */
        [data-testid="stSidebar"] .stRadio > div {
            gap: 0.3rem !important;
        }

        /* Expander styling */
        [data-testid="stSidebar"] div[data-testid="stExpander"] summary p {
            font-weight: 600 !important;
            color: #94a3b8 !important;
        }
        [data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover p {
            color: #ffffff !important;
        }

        /* Remove default expander borders */
        [data-testid="stSidebar"] div[data-testid="stExpander"],
        [data-testid="stSidebar"] div[data-testid="stExpander"] > details,
        [data-testid="stSidebar"] div[data-testid="stExpander"] summary {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] div[data-testid="stExpander"] > details > div {
            border: none !important;
            background-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Sidebar header (Navigation) ---
    st.sidebar.markdown("## Navigation")

    # --- Top main options (no expander) ---
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

    # --- COT Data expander ---
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

    # --- Macro Scanners expander ---
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

    # --- Seasonality Scanners expander ---
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

    # --- Crowd Sentiment expander ---
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

    # --- Bottom main options (no expander) ---
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

    # --- Admin options (if admin) ---
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

    # --- User info and logout ---
    if st.session_state.get("user_email"):
        user_name = st.session_state.user_email.split("@")[0]
        st.sidebar.markdown(f"Hello, **{user_name}**")
    if st.sidebar.button("Logout"):
        try:
            supabase_auth.auth.sign_out()
        except:
            pass
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.user_email = None
        st.rerun()
