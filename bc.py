#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import openpyxl
import json
import glob
import io
import time
import plotly.graph_objects as go
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from calendar import month_abbr
import re
from datetime import datetime, timedelta
import cloudscraper
from tradingview_ta import TA_Handler, Interval
from supabase import create_client, Client

try:
    import cot_reports as cot_reports_lib

    COT_AVAILABLE = True
except ImportError:
    COT_AVAILABLE = False














# ✅ NEW: Hide Streamlit header only on unauthenticated pages (landing / auth)


# ======================= INITIALIZE ANALYZER =======================
@st.cache_resource
def init_analyzer():
    analyzer = CurrencyFundamentalAnalyzer(supabase_admin)
    analyzer.load_data()
    return analyzer


analyzer = init_analyzer()

# ✅ SHOW LOADING ANIMATION ON FIRST LOAD AFTER LOGIN
if "initial_loading_done" not in st.session_state:
    st.session_state.initial_loading_done = False

if not st.session_state.initial_loading_done:
    with st.spinner("🔄 Loading MacroPulse... Preparing your dashboard"):
        time.sleep(4)  # 4 seconds of smooth animation
    st.session_state.initial_loading_done = True

# Ensure sidebar starts expanded
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"



# ======================= SIDEBAR NAVIGATION =======================

# Initialize global active page
if "active_page" not in st.session_state:
    st.session_state.active_page = "🏆 Top Setups"

# Sidebar header with "Navigation" and close button
if st.session_state.sidebar_visible:
    col_nav, col_close = st.sidebar.columns([8, 1])
    with col_nav:
        st.markdown("## Navigation")
    with col_close:
        if st.button("◀", key="sidebar_collapse", help="Hide Sidebar"):
            st.session_state.sidebar_visible = False
            st.rerun()
else:
    st.sidebar.markdown("## Navigation")

# Define navigation lists
nav_main_top = [
    "🏆 Top Setups",
    "📋 Asset Scorecard",
    "📊 Forex Scorecard",
]
nav_cot_data = [
    "📉 Latest COT Report",
    "📈 COT Trends",
    "📊 COT Data history",
]
nav_macro_scanners = [
    "📈 Eco surprise index",
    "🌍 Economic Strength Index",
]
nav_seasonality_scanners = [
    "📅 Monthly Seasonality",
    "📈 Annual Seasonality",
]
nav_crowd_sentiment = [
    "🔄 Retail Sentiment",
    "📊Put-Call Ratio",
]
nav_main_bottom = [
    "🔥 Economic Heatmap",
    "📅 Economic calendar",
    "🔄 Reload Data",
]
nav_options_admin = [
    "✏️ Data Updates",
    "⚙️ Trend Settings",
    "👥 User Approvals",
]

is_admin = st.session_state.get("is_admin", False)


# Synchronization callback
def sync_navigation(clicked_key):
    # Set the global active page to whatever was just clicked
    st.session_state.active_page = st.session_state[clicked_key]
    # Clear all other radio groups to remove grey backgrounds
    for key in [
        "nav_top",
        "nav_cot",
        "nav_macro",
        "nav_season",
        "nav_crowd",
        "nav_bottom",
        "nav_admin",
    ]:
        if key != clicked_key:
            st.session_state[key] = None


# Helper to get index if active_page belongs to a list, else None
def get_index(page_list):
    if st.session_state.active_page in page_list:
        return page_list.index(st.session_state.active_page)
    return None


# 1. Top main options (no expander)
st.sidebar.radio(
    "nav_top",
    nav_main_top,
    key="nav_top",
    index=get_index(nav_main_top),
    on_change=sync_navigation,
    args=("nav_top",),
    label_visibility="collapsed",
)
# 2. COT data expander
is_cot_active = st.session_state.active_page in nav_cot_data
with st.sidebar.expander("👥 COT Data", expanded=is_cot_active):
    st.radio(
        "nav_cot",
        nav_cot_data,
        key="nav_cot",
        index=get_index(nav_cot_data),
        on_change=sync_navigation,
        args=("nav_cot",),
        label_visibility="collapsed",
    )


# 3. Macro Scanners expander
is_macro_active = st.session_state.active_page in nav_macro_scanners
with st.sidebar.expander("🔎 Macro Scanners", expanded=is_macro_active):
    st.radio(
        "nav_macro",
        nav_macro_scanners,
        key="nav_macro",
        index=get_index(nav_macro_scanners),
        on_change=sync_navigation,
        args=("nav_macro",),
        label_visibility="collapsed",
    )

# 4. Seasonality Scanners expander
is_season_active = st.session_state.active_page in nav_seasonality_scanners
with st.sidebar.expander("🍂 Seasonality Scanners", expanded=is_season_active):
    st.radio(
        "nav_season",
        nav_seasonality_scanners,
        key="nav_season",
        index=get_index(nav_seasonality_scanners),
        on_change=sync_navigation,
        args=("nav_season",),
        label_visibility="collapsed",
    )

# 5. Crowd Sentiment expander (NEW)
is_crowd_active = st.session_state.active_page in nav_crowd_sentiment
with st.sidebar.expander("👥 Crowd Sentiment", expanded=is_crowd_active):
    st.radio(
        "nav_crowd",
        nav_crowd_sentiment,
        key="nav_crowd",
        index=get_index(nav_crowd_sentiment),
        on_change=sync_navigation,
        args=("nav_crowd",),
        label_visibility="collapsed",
    )

# 6. Bottom main options (no expander)
st.sidebar.radio(
    "nav_bottom",
    nav_main_bottom,
    key="nav_bottom",
    index=get_index(nav_main_bottom),
    on_change=sync_navigation,
    args=("nav_bottom",),
    label_visibility="collapsed",
)

# 7. Admin options (if admin)
if is_admin:
    st.sidebar.radio(
        "nav_admin",
        nav_options_admin,
        key="nav_admin",
        index=get_index(nav_options_admin),
        on_change=sync_navigation,
        args=("nav_admin",),
        label_visibility="collapsed",
    )

st.sidebar.markdown("---")

if st.session_state.user_email:
    user_name = st.session_state.user_email.split("@")[0]
    st.sidebar.markdown(f"Hello, **{user_name}**")
if st.sidebar.button("Logout"):
    sign_out()

st.sidebar.markdown("---")

# Set the page variable for the rest of the app
page = st.session_state.active_page

if st.session_state.success_msg:
    st.markdown(
        f'<div class="success-message">✅ {st.session_state.success_msg}</div>',
        unsafe_allow_html=True,
    )
    st.session_state.success_msg = None

# Header row with title and expand button (only visible when sidebar is hidden)
col_title, col_toggle = st.columns([8, 2])
with col_title:
    st.markdown('<div class="main-header">📊 MacroPulse</div>', unsafe_allow_html=True)
with col_toggle:
    if not st.session_state.sidebar_visible:
        if st.button("Open Sidebar", key="sidebar_expand", help="Show Sidebar"):
            st.session_state.sidebar_visible = True
            st.rerun()

# ======================= PAGE RENDERING =======================
page = st.session_state.active_page












# Fallback for unauthorized admin pages
elif (
    page
    in [
        "✏️ Data Updates",
        "📅 Seasonality Config",
        "⚙️ Trend Settings",
        "👥 User Approvals",
    ]
    and not is_admin
):
    st.error("You must be logged in as admin to access this page.")
    st.stop()