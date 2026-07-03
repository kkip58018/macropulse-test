import streamlit as st
import time
from streamlit_cookies_controller import CookieController
from db import supabase_auth, supabase_admin, save_session,get_session_file,load_session
from analyzer import init_analyzer

# ======================= PRE-CONFIG CHECK =======================
# Check auth status BEFORE configuring the page to dynamically set sidebar
is_authenticated = st.session_state.get("authenticated", False)

st.set_page_config(
    page_title="MacroPulse",
    layout="wide",
    initial_sidebar_state="expanded" if is_authenticated else "collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

controller = CookieController()

# Check if a login cookie exists
if "authenticated" not in st.session_state:
    if controller.get("user_logged_in") == "true":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

# ======================= GLOBAL STYLES =======================
st.markdown(
    """
<style>
    /* Hide toolbar and decoration */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* Base app background */
    .stApp {
        background-color: #0b0f15;
        padding-top: 0 !important;
    }

    /* Default: no extra padding for unauthenticated pages (header hidden) */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* When authenticated, the header is visible so we need space */
    .stApp[data-testid="stApp"] .block-container {
        /* Overridden later if authenticated */
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f131a;
        border-right: 1px solid #1e2430;
    }
    
    /* Sticky Navbar (your custom landing nav) */
    .landing-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background-color: #0f131a;
        border-bottom: 1px solid #1e2430;
        position: sticky;
        top: 0;
        z-index: 999;
        margin: 0;
    }
    .landing-logo {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .nav-links {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    .nav-links a {
        color: #94a3b8;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    .nav-links a:hover {
        color: #ffffff;
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        max-width: 900px;
        margin: 0 auto;
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.3rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    /* Value Section */
    .value-section {
        padding: 4rem 2rem;
        background-color: #0f131a;
        border-top: 1px solid #1e2430;
        border-bottom: 1px solid #1e2430;
        margin: 2rem 0;
    }
    .value-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .value-card {
        text-align: center;
        padding: 1.5rem;
    }
    .value-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .value-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .value-desc {
        color: #94a3b8;
    }
    
    /* Features Section */
    .features-section {
        padding: 4rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 3rem;
    }
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
    }
    .feature-card {
        background-color: #0f131a;
        border: 1px solid #1e2430;
        border-radius: 12px;
        padding: 1.5rem;
        transition: transform 0.2s, border-color 0.2s;
    }
    .feature-card:hover {
        border-color: #00ff88;
        transform: translateY(-3px);
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    
    /* Footer */
    .footer {
        background-color: #0f131a;
        border-top: 1px solid #1e2430;
        padding: 2rem;
        text-align: center;
        color: #64748b;
        margin-top: 3rem;
    }
    
    /* ---------- AUTH CONTAINER (FIXED) ---------- */
    /*.auth-container {
        max-width: 450px !important;
        width: 90% !important;
        margin: 3rem auto !important;
        background-color: #0f131a !important;
        border: 1px solid #1e2430 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }*/

    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .auth-header h2 {
        color: #ffffff !important;
        margin-bottom: 0.5rem !important;
        font-size: 2rem !important;
    }

    .auth-header p {
        color: #94a3b8 !important;
    }

    /* Fix for Streamlit form elements inside auth container */
    .auth-container .stTextInput > div > div > input {
        background-color: #1e2430 !important;
        color: white !important;
        border: 1px solid #2a3340 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
    }

    .auth-container .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00b8ff) !important;
        color: #0b0f15 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        width: 100% !important;
        transition: opacity 0.2s;
    }

    .auth-container .stButton > button:hover {
        opacity: 0.9 !important;
    }

    .auth-container .stTabs [data-baseweb="tab-list"] {
        gap: 2rem !important;
        justify-content: center !important;
        border-bottom: 1px solid #1e2430 !important;
        margin-bottom: 1.5rem !important;
    }

    .auth-container .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }

    .auth-container .stTabs [aria-selected="true"] {
        color: #00ff88 !important;
    }

    /* Remove any unwanted black bars above header */
    .auth-container + div {
        display: none !important;
    }

    div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: 0 !important;
    }

    /* Main app header */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        margin-top: 0;
    }
    
    /* Dataframe styling */
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    .dataframe th { background-color: #1e2430 !important; color: #94a3b8 !important; font-weight: 600; padding: 8px 12px !important; }
    .dataframe td { padding: 4px 12px !important; border-bottom: 1px solid #1e293b; line-height: 1.2 !important; }
    .dataframe tr:hover { background-color: #1a1f2e !important; }
    .success-message {
        background-color: #1e3a2e;
        color: #00ff88;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #00ff88;
    }
    .score-card {
        background-color: #1a1f2e;
        border-radius: 8px;
        padding: 0.5rem;
        margin-bottom: 0.6rem;
        text-align: center;
        border-left: 3px solid;
    }
    .score-number {
        font-size: 1rem;
        font-weight: bold;
    }
    .score-card div:first-child {
        font-size: 0.7rem;
        opacity: 0.7;
    }
    .score-card div:last-child {
        font-size: 0.7rem;
    }
    /* Spinner overlay styling */
    .stSpinner > div {
    border-top-color: #00ff88 !important;
    }
     /* Sidebar toggle button styling */
    div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) {
        align-items: center;
    }
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #2a3340 !important;
        color: #94a3b8 !important;
        font-size: 18px !important;
        padding: 4px 8px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #1e2430 !important;
        color: white !important;
    }
    /* ================= SIDEBAR NAVIGATION CLEANUP ================= */
    
    /* 1. Remove all borders and shadows from the expander container */
    [data-testid="stSidebar"] div[data-testid="stExpander"],
    [data-testid="stSidebar"] div[data-testid="stExpander"] > details,
    [data-testid="stSidebar"] div[data-testid="stExpander"] summary {
        border: none !important;
        border-color: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Remove border from the opened expander content area box */
    [data-testid="stSidebar"] div[data-testid="stExpander"] > details > div {
        border: none !important;
        background-color: transparent !important;
    }

    /* Style the Expander Header Text */
    [data-testid="stSidebar"] div[data-testid="stExpander"] summary p {
        font-weight: 600 !important;
        color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover p {
        color: #ffffff !important;
    }

    /* 2. Style Radio Button Menus */
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.3rem !important;
    }
    
    /* Hide the radio button native circles entirely */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* Reset the parent label container completely */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        padding: 0 !important;
        margin: 0 0 2px 0 !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Target the text wrapper directly for the base/inactive state */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input + div {
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        width: 100% !important;
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
    
    /* ACTIVE / SELECTED NAVIGATION STATE */
    /* Only targets the text div right next to a genuinely checked input */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div {
        background-color: #374151 !important; /* Solid grey active background */
    }
    
    /* Active text highlight */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label input:checked + div p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
     /* Hide the "app" link (first item) */
    [data-testid="stSidebarNavItems"] > li:first-child {
    display: none !important;
    }

    /* Increase font size of all sidebar nav links */
    [data-testid="stSidebarNavItems"] a p {
    font-size: 1.3rem !important;   /* adjust as needed */
    font-weight: 500 !important;
    color: #e2e8f0 !important;
    }

   /* Active page highlight */
    [data-testid="stSidebarNavItems"] a[aria-current="page"] p {
    color: #00ff88 !important;
    font-weight: 700 !important;
    }
    [data-testid="stSidebarNavItems"] li:has(span[label="app"]) {
    display: none !important;
    }
</style>
""",
    unsafe_allow_html=True,
)
# CSS to completely hide the sidebar toggle and container if NOT logged in
if not is_authenticated:
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# ======================= STATE INITIALIZATION =======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_auth" not in st.session_state:
    st.session_state.show_auth = False
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# Pre-warm the analyzer instance in the cache
analyzer = init_analyzer()

# ======================= AUTHENTICATION LOGIC =======================
def sign_in(email, password):
    try:
        response = supabase_auth.auth.sign_in_with_password({"email": email, "password": password})
        if response and response.session:
            
            # 1. Check admin and approval status FIRST
            user_id = response.user.id
            profile = supabase_admin.table("user_profiles").select("approved, is_admin").eq("id", user_id).execute()
            
            if profile.data:
                # If they are not approved, boot them out BEFORE setting any cookies
                if not profile.data[0].get("approved", False):
                    supabase_auth.auth.sign_out() # Optional but good practice: wipe the supabase session 
                    return False, "Account pending approval. Please contact an admin."
                
                # Check if they are an admin
                if profile.data[0].get("is_admin", False):
                    st.session_state.is_admin = True
            else:
                return False, "User profile not found in database."

            save_session(response.session, email)
            # When login is successful
            st.session_state.authenticated = True
            # Put a flag in the browser's URL (e.g., yoursite.com/?auth=true)
            st.query_params["auth"] = "true" 
            st.switch_page("pages/01_Top_Setups.py")
            
            return True, "Success"
            
        return False, "Invalid credentials"
    except Exception as e:
        return False, f"Login error: {str(e)}"  

def sign_up(email, password):
    try:
        response = supabase_auth.auth.sign_up({"email": email, "password": password})
        if response and response.user:
            return True, "Registration successful! Your account is pending admin approval."
        return False, "Registration failed."
    except Exception as e:
        return False, f"Signup error: {str(e)}"

# ======================= LANDING PAGE =======================
def show_landing_page():
    # CSS with reliable typewriter effect + contact section styling
    st.markdown(
        """
    <style>
    /* Typewriter container */
    .typewriter-wrapper {
        text-align: center;
        margin-bottom: 1rem;
    }
    .typewriter {
        display: inline-block;
        overflow: hidden;
        border-right: 3px solid #00ff88;
        white-space: nowrap;
        margin: 0 auto;
        animation: typing 3.5s steps(40, end) forwards,
                   blink-caret 0.75s step-end infinite;
        font-size: clamp(2rem, 8vw, 3.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: #00ff88; /* fallback */
        line-height: 1.2;
        width: 0;
    }
    @keyframes typing {
        from { width: 0; }
        to { width: 100%; }
    }
    @keyframes blink-caret {
        from, to { border-color: transparent; }
        50% { border-color: #00ff88; }
    }

    /* Fade in for subtitle and CTA */
    @keyframes fadeInUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .hero-subtitle-animated {
        font-size: 1.3rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        text-align: center;
        animation: fadeInUp 0.8s ease-out 0.5s forwards;
        opacity: 0;
        animation-fill-mode: forwards;
    }
    .cta-button-wrapper {
        text-align: center;
        animation: fadeInUp 0.8s ease-out 1s forwards;
        opacity: 0;
        animation-fill-mode: forwards;
    }
    
    /* Social proof section */
    .social-proof-section {
        padding: 2rem 2rem 4rem 2rem;
        max-width: 1000px;
        margin: 0 auto;
        text-align: center;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin-top: 2rem;
    }
    .stat-item {
        background-color: #0f131a;
        border: 1px solid #1e2430;
        border-radius: 16px;
        padding: 1.5rem;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    .quote-text {
        font-size: 1.2rem;
        color: #e2e8f0;
        font-style: italic;
        margin-bottom: 1rem;
    }
    .quote-author {
        color: #00ff88;
        font-weight: 500;
    }

    /* Contact Section */
    .contact-section {
        padding: 4rem 2rem;
        max-width: 800px;
        margin: 0 auto;
        text-align: center;
        background-color: #0b0f15;
        border-top: 1px solid #1e2430;
    }
    .contact-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .contact-subtitle {
        color: #94a3b8;
        font-size: 1.2rem;
        margin-bottom: 2.5rem;
    }
    .contact-card {
        background-color: #0f131a;
        border: 1px solid #1e2430;
        border-radius: 16px;
        padding: 2rem;
        display: inline-block;
        text-align: left;
        max-width: 500px;
        width: 100%;
    }
    .contact-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .contact-icon {
        font-size: 1.8rem;
        width: 2.5rem;
        text-align: center;
    }
    .contact-detail {
        color: #e2e8f0;
        font-size: 1.1rem;
    }
    .contact-detail a {
        color: #00ff88;
        text-decoration: none;
        transition: color 0.2s;
    }
    .contact-detail a:hover {
        color: #00b8ff;
        text-decoration: underline;
    }
    .contact-note {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 1.5rem;
        text-align: center;
    }

    /* Mobile fallback */
    @media (max-width: 600px) {
        .typewriter {
            white-space: normal;
            border-right: none;
            animation: none;
            width: auto;
            font-size: 2rem;
        }
        .contact-card {
            padding: 1.5rem;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Custom navbar
    col1, col2, col3 = st.columns([2, 5, 1])
    with col1:
        st.markdown(
            '<div class="landing-logo">📊 MacroPulse</div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
        <div class="nav-links" style="justify-content: center; padding-top: 0.5rem;">
            <a href="#features">Features</a>
            <a href="#value">Why Us</a>
            <a href="#contact">Contact</a>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        if st.button("🔐 Login", key="nav_login_btn", use_container_width=True):
            st.session_state.show_auth = True
            st.rerun()

    # Hero Section
    st.markdown(
        """
    <div class="hero-section">
        <div class="typewriter-wrapper">
            <div class="typewriter">Trade with Institutional Clarity</div>
        </div>
        <div class="hero-subtitle-animated">Stop guessing. Start trading with a data‑driven edge that combines institutional positioning, macro surprises, and seasonal patterns into one clear direction.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # CTA Button
    st.markdown('<div class="cta-button-wrapper">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🚀 Get Started — It's Free", use_container_width=True, key="cta_button"
        ):
            st.session_state.show_auth = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Value Proposition (3 cards)
    st.markdown(
        """
    <div class="value-section" id="value">
        <div class="value-grid">
            <div class="value-card">
                <div class="value-icon">🏦</div>
                <div class="value-title">Trade What the Smart Money Sees</div>
                <div class="value-desc">COT positioning, retail sentiment, and macro surprises — the same data hedge funds use, now accessible to you in seconds.</div>
            </div>
            <div class="value-card">
                <div class="value-icon">📈</div>
                <div class="value-title">Spot High‑Probability Setups Instantly</div>
                <div class="value-desc">Our scoring system surfaces the most compelling long and short opportunities, saving you hours of manual analysis every week.</div>
            </div>
            <div class="value-card">
                <div class="value-icon">⏱️</div>
                <div class="value-title">From Hours to Seconds</div>
                <div class="value-desc">Stop manually checking economic calendars, COT reports, and charts. MacroPulse does the heavy lifting so you can focus on execution.</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Social Proof / Metrics Section
    st.markdown(
        """
    <div class="social-proof-section">
        <div class="quote-text">"MacroPulse has completely changed how I approach forex. The combined score gives me conviction I never had before."</div>
        <div class="quote-author">— Michael R., Full‑Time Trader</div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number">28</div>
                <div class="stat-label">Currency Pairs Covered</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">5</div>
                <div class="stat-label">Independent Factors Combined</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">100%</div>
                <div class="stat-label">Cloud‑Based & Secure</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Features Section (5 cards)
    st.markdown(
        """
    <div class="features-section" id="features">
        <div class="section-title">Everything You Need to Trade Smarter</div>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Deep‑Dive Scorecard</div>
                <div class="feature-desc">Click any pair to see exactly why it scored the way it did. Understand the "why" behind every recommendation.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🌡️</div>
                <div class="feature-title">Currency Strength at a Glance</div>
                <div class="feature-desc">Intuitive heatmap and gauges show which currencies are fundamentally strong or weak — no spreadsheet required.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Institutional COT Tracker</div>
                <div class="feature-desc">See how the "big money" is positioned and how it's changing week‑to‑week. Never trade against the dominant flow again.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📆</div>
                <div class="feature-title">Live Economic Radar</div>
                <div class="feature-desc">Plan your week around high‑impact news. Update actuals with one click and watch the scores adjust automatically.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🍂</div>
                <div class="feature-title">Seasonal Edge</div>
                <div class="feature-desc">Leverage historical monthly biases and recurring trend windows. Trade with the calendar, not against it.</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Contact Section
    st.markdown(
        """
    <div class="contact-section" id="contact">
        <div class="contact-title">Get in Touch</div>
        <div class="contact-subtitle">Have questions? We're here to help.</div>
        <div class="contact-card">
            <div class="contact-item">
                <div class="contact-icon">📧</div>
                <div class="contact-detail">
                    <a href="https://mail.google.com/mail/?view=cm&fs=1&to=kkip58018@gmail.com">support@macropulse.io</a>
                </div>
            </div>
            <div class="contact-item">
                <div class="contact-icon">💬</div>
                <div class="contact-detail">
                    <a href="https://chat.whatsapp.com/LwqzoUatXMCHzRRCoQRtFG?mode=gi_t" target="https://chat.whatsapp.com/LwqzoUatXMCHzRRCoQRtFG?mode=gi_t">Join our WhatsApp Community</a>
                </div>
            </div>
            <div class="contact-item">
                <div class="contact-icon">🐦</div>
                <div class="contact-detail">
                    <a href="#" target="_blank">Follow @MacroPulse</a>
                </div>
            </div>
            <div class="contact-note">
                We typically respond within 24 hours.
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Footer
    st.markdown(
        """
    <div class="footer">
        <p>© 2025 MacroPulse. All rights reserved. | <a href="#" style="color: #64748b; text-decoration: none;">Privacy Policy</a> | <a href="#" style="color: #64748b; text-decoration: none;">Terms of Service</a></p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">Forex trading involves substantial risk. Past performance does not guarantee future results.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ======================= AUTHENTICATION PAGE =======================
def show_auth_page():
    # Initialize auth mode if not set
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # CSS for card layout and outline buttons (same as before)
    st.markdown(
        """
    <style>
        header[data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
        }
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            max-width: 900px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .stApp {
            background-color: #0b0f15 !important;
        }
        .auth-card {
            background-color: #0f131a !important;
            border: 1px solid #1e2430 !important;
            border-radius: 16px !important;
            padding: 2rem !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5) !important;
            margin-top: 2rem !important;
        }
        .auth-title {
            text-align: center;
            color: white;
            font-size: 2rem;
            margin-bottom: 2.5rem;
            margin-top: 200px;
        }
        div[data-testid="stTextInput"] input {
            background-color: #1e2430 !important;
            color: white !important;
            border: 1px solid #2a3340 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
        }
        div[data-testid="stFormSubmitButton"] > button {
            background: transparent !important;
            color: white !important;
            font-weight: bold !important;
            border: 1px solid grey !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            width: 100% !important;
            transition: all 0.2s !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background: #3c3c3c !important;
            border-color: #00b8ff !important;
        }
        .toggle-btn-container {
            text-align: center;
            margin-top: 1.0rem;
        }
        .toggle-btn-container button {
            background: transparent !important;
            color: #00ff88 !important;
            border: none !important;
            font-weight: 500;
            padding: 0 !important;
            margin: 0 !important;
            text-decoration: none;
        }
        .toggle-btn-container button:hover {
            text-decoration: underline !important;
            color: #00b8ff !important;
        }
        div[data-testid="stButton"] > button {
            background: transparent !important;
            color: #94a3b8 !important;
            border: 1px solid #2a3340 !important;
            border-radius: 8px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.auth_mode == "login":
        st.markdown(
            '<div class="auth-title">Welcome Back</div>', unsafe_allow_html=True
        )
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
            
            if submitted:
                # Added .strip() to prevent accidental spaces from breaking auth
                success, msg = sign_in(email.strip(), password) 
                if success:
                    st.session_state.authenticated = True
                    st.session_state.show_auth = False
                    st.success("Login successful! Redirecting...")
                    time.sleep(0.5) 
                    
                    # 🔄 REPLACED st.switch_page with st.rerun()
                    st.rerun() 
                else:
                    st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

        # Toggle to Sign Up
        st.markdown('<div class="toggle-btn-container">', unsafe_allow_html=True)
        if st.button("Don't have an account? Sign up", key="switch_to_signup"):
            st.session_state.auth_mode = "signup"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:  # signup mode
        st.markdown(
            '<div class="auth-title">Create Account</div>', unsafe_allow_html=True
        )

        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input(
                "Password", type="password", key="signup_password"
            )
            confirm = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            submitted = st.form_submit_button("Register")
            if submitted:
                if new_password != confirm:
                    st.error("Passwords do not match")
                else:
                    success, msg = sign_up(new_email, new_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

        # Toggle to Login
        st.markdown('<div class="toggle-btn-container">', unsafe_allow_html=True)
        if st.button("← Back to Login", key="switch_to_login"):
            st.session_state.auth_mode = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Back to Home button (outside card)
    if st.button("← Back to Home"):
        st.session_state.show_auth = False
        st.session_state.auth_mode = "login"
        st.rerun()


# ======================= MAIN APP ROUTING =======================
if not st.session_state.authenticated:
    # If not logged in, show the gatekeeper screens and halt execution
    if st.session_state.show_auth:
        show_auth_page()
    else:
        show_landing_page()
    st.stop()

st.switch_page("pages/01_Top_Setups.py")



