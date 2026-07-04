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
    "04_Latest_COT_Report": "📉 Latest COT Report",
    "05_COT_Trends": "📈 COT Trends",
    "06_COT_Data_History": "📊 COT Data history",
    "07_Eco_Suprise_Index": "📈 Eco surprise index",
    "08_Eco_Strength_Index": "🌍 Economic Strength Index",
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

def inject_theme_css():
    """Injects the global dark mode styling required by all pages."""
    st.markdown(
        """
    <style>
        /* Hide toolbar and decoration */
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        
        /* Base app background */
        .stApp {
            background-color: #0b0f15;
            padding-top: 0 !important;
        }
        
        /* Sidebar container styling */
        [data-testid="stSidebar"] {
            background-color: #0f131a !important;
            border-right: 1px solid #1e2430 !important;
        }
        
        /* Hide default sidebar nav links */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* --- Your custom Expander & Radio Navigation Styling --- */
        [data-testid="stSidebar"] div[data-testid="stExpander"],
        [data-testid="stSidebar"] div[data-testid="stExpander"] > details,
        [data-testid="stSidebar"] div[data-testid="stExpander"] summary {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input + div {
            padding: 0.6rem 1rem !important;
            border-radius: 8px !important;
        }

        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div {
            background-color: #374151 !important; /* Retain solid grey selection color */
        }
        
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Hide native radio circles */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {
            display: none !important;
        }
        /* Force the 'Open Sidebar' button to be visible and white on dark backgrounds */
        [data-testid="collapsedControl"] {
            display: flex !important;
            z-index: 999999 !important;
        }
        
        [data-testid="collapsedControl"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        /* Ensure the button has a slight hover effect so it feels clickable */
        [data-testid="collapsedControl"]:hover {
            background-color: rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

def render():
    inject_theme_css()
    
    # --- Ensure sidebar_visible is in session state ---
    if "sidebar_visible" not in st.session_state:
        st.session_state.sidebar_visible = True  # start open

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

    # --- Custom CSS for header and button ---
    st.markdown(
        """
        <style>
        /* Main header title */
        .main-header {
            font-size: 2.4rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #00ff88, #00b8ff) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            margin-bottom: 0.5rem !important;
            margin-top: 0 !important;
        }
        
        /* Open Sidebar button styling */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            background-color: transparent !important;
            border: 1px solid #2a3340 !important;
            color: #94a3b8 !important;
            font-size: 16px !important;
            padding: 8px 16px !important;
            border-radius: 6px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
            background-color: #1e2430 !important;
            color: #ffffff !important;
            border-color: #00b8ff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Render the main header row (title + toggle button) ---
    sidebar_visible = st.session_state.sidebar_visible
    col_title, col_toggle = st.columns([8, 2])
    with col_title:
        st.markdown('<div class="main-header">📊 MacroPulse</div>', unsafe_allow_html=True)
    with col_toggle:
        if not sidebar_visible:
            if st.button("Open Sidebar", key="sidebar_expand", help="Show Sidebar"):
                st.session_state.sidebar_visible = True
                st.rerun()

    # --- Sidebar content ---
    # Sidebar header with close button (if visible)
    if sidebar_visible:
        col_nav, col_close = st.sidebar.columns([8, 1])
        with col_nav:
            st.sidebar.markdown("## Navigation")
        with col_close:
            if st.button("◀", key="sidebar_collapse", help="Hide Sidebar"):
                st.session_state.sidebar_visible = False
                st.rerun()
    else:
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
