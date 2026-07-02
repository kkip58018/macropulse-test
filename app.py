

import streamlit as st
import time
from db import supabase_auth, supabase_admin
from analyzer import init_analyzer
from db import save_session

# ======================= PRE-CONFIG CHECK =======================
is_authenticated = st.session_state.get("authenticated", False)

st.set_page_config(
    page_title="MacroPulse",
    layout="wide",
    initial_sidebar_state="expanded" if is_authenticated else "collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ======================= GLOBAL & SIDEBAR STYLES =======================
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

    /* Default padding removal */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* ---------------- CUSTOM SIDEBAR FIXES ---------------- */
    /* BRUTE FORCE: Hide the first link (app.py) from the sidebar menu */
    [data-testid="stSidebarNav"] ul li:nth-child(1),
    [data-testid="stSidebarNavItems"] li:nth-child(1) {
        display: none !important;
    }
    
    /* Hide any top title/header container generated inside the nav */
    [data-testid="stSidebarNav"] > div:first-child {
        display: none !important;
    }
    
    /* INCREASE PADDING AND SPACING for the clickable link boxes */
    [data-testid="stSidebarNav"] ul li a,
    [data-testid="stSidebarNavItems"] li a {
        padding: 1rem 1.2rem !important;  /* Bumping up the padding inside the link */
        margin-bottom: 0.5rem !important; /* Adding space between each link */
    }
    
    /* INCREASE FONT SIZE of all sidebar navigation text */
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNavItems"] a span {
        font-size: 1.3rem !important; /* Noticeably larger font */
        font-weight: 500 !important;
        color: #e2e8f0 !important;
    }
    
    /* Style the CURRENTLY ACTIVE sidebar link */
    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNavItems"] a[aria-current="page"] span {
        font-size: 1.4rem !important; /* Active link is even larger */
        color: #00ff88 !important;
        font-weight: 700 !important;
    }
    /* ----------------------------------------------------- */
    /* Sticky Navbar */
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
    .nav-links { display: flex; gap: 2rem; align-items: center; }
    .nav-links a { color: #94a3b8; text-decoration: none; font-weight: 500; transition: color 0.2s; }
    .nav-links a:hover { color: #ffffff; }
    
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
    .hero-subtitle { font-size: 1.3rem; color: #94a3b8; margin-bottom: 2rem; }
    
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
    .value-card { text-align: center; padding: 1.5rem; }
    .value-icon { font-size: 2.5rem; margin-bottom: 1rem; }
    .value-title { font-size: 1.5rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem; }
    .value-desc { color: #94a3b8; }
    
    /* Features Section */
    .features-section { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
    .section-title { text-align: center; font-size: 2.5rem; font-weight: 700; color: #ffffff; margin-bottom: 3rem; }
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
    .feature-card:hover { border-color: #00ff88; transform: translateY(-3px); }
    .feature-icon { font-size: 2rem; margin-bottom: 1rem; }
    .feature-title { font-size: 1.3rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem; }
    .feature-desc { color: #94a3b8; font-size: 0.95rem; }
    
    /* Social Proof Section */
    .social-proof-section {
        padding: 4rem 2rem;
        max-width: 1000px;
        margin: 0 auto;
        text-align: center;
    }
    .quote-text { font-size: 1.2rem; color: #e2e8f0; font-style: italic; margin-bottom: 1rem; }
    .quote-author { color: #00ff88; font-weight: 500; }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin-top: 3rem;
    }
    .stat-item .stat-number { font-size: 2.5rem; font-weight: 700; color: #ffffff; }
    .stat-item .stat-label { color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem; }

    /* Contact Section */
    .contact-section {
        padding: 4rem 2rem;
        max-width: 800px;
        margin: 0 auto;
        text-align: center;
        background-color: #0b0f15;
        border-top: 1px solid #1e2430;
    }
    .contact-title { font-size: 2.5rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem; }
    .contact-subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
    
    /* Footer */
    .footer {
        background-color: #0f131a;
        border-top: 1px solid #1e2430;
        padding: 2rem;
        text-align: center;
        color: #64748b;
        margin-top: 3rem;
    }
    
    /* AUTH CONTAINER */
    .auth-header { text-align: center; margin-bottom: 2rem; }
    .auth-header h2 { color: #ffffff !important; margin-bottom: 0.5rem !important; font-size: 2rem !important; }
    .auth-header p { color: #94a3b8 !important; }

    .stTextInput > div > div > input {
        background-color: #1e2430 !important;
        color: white !important;
        border: 1px solid #2a3340 !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00b8ff) !important;
        color: #0b0f15 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        width: 100% !important;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.9 !important; }
    
    .toggle-btn-container { text-align: center; margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# CSS to completely hide sidebar elements when not logged in
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
            save_session(response.session, email)
            
            user_id = response.user.id
            profile = supabase_admin.table("user_profiles").select("approved, is_admin").eq("id", user_id).execute()
            if profile.data:
                if not profile.data[0].get("approved", False):
                    return False, "Account pending approval. Please contact an admin."
                if profile.data[0].get("is_admin", False):
                    st.session_state.is_admin = True
            else:
                return False, "User profile not found in database."
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

# ======================= UI COMPONENTS =======================
def show_landing_page():
    st.markdown("""
    <nav class="landing-nav">
        <div class="landing-logo">MacroPulse</div>
        <div class="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#pricing">Pricing</a>
        </div>
    </nav>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Institutional-Grade Macroeconomic Intelligence</h1>
        <p class="hero-subtitle">Aggregating fundamental data, COT positioning, and retail sentiment to uncover high-probability forex setups.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("Enter Dashboard", use_container_width=True):
            st.session_state.show_auth = True
            st.rerun()

    st.markdown("""
    <div class="value-section">
        <div class="value-grid">
            <div class="value-card">
                <div class="value-icon">🧠</div>
                <div class="value-title">Algorithmic Scoring</div>
                <div class="value-desc">Eliminate emotional bias with our proprietary 1-10 scoring system for 28 major forex pairs based on deep fundamental metrics.</div>
            </div>
            <div class="value-card">
                <div class="value-icon">🏦</div>
                <div class="value-title">Smart Money Tracking</div>
                <div class="value-desc">Follow institutional flows with integrated Commitment of Traders (COT) report analysis updated automatically.</div>
            </div>
            <div class="value-card">
                <div class="value-icon">⏱️</div>
                <div class="value-title">From Hours to Seconds</div>
                <div class="value-desc">Stop manually checking economic calendars, COT reports, and charts. MacroPulse does the heavy lifting so you can focus on execution.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="features-section" id="features">
        <h2 class="section-title">Comprehensive Market Analysis</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Top Trade Setups</div>
                <div class="feature-desc">Instantly identify the strongest and weakest currencies to form high-probability pairings.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📋</div>
                <div class="feature-title">Global Asset Scorecard</div>
                <div class="feature-desc">A unified dashboard tracking growth, inflation, and employment bias across major economies.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📉</div>
                <div class="feature-title">Contrarian Retail Sentiment</div>
                <div class="feature-desc">Capitalize on retail trader positioning data to identify market extremes and potential reversals.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📅</div>
                <div class="feature-title">10-Year Seasonality</div>
                <div class="feature-desc">Leverage historical data to identify statistically significant monthly and annual trends.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="social-proof-section">
        <div class="quote-text">"MacroPulse has completely changed how I approach forex. The combined score gives me conviction I never had before."</div>
        <div class="quote-author">— Michael R., Full‑Time Trader</div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number">28</div>
                <div class="stat-label">Currency Pairs</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">15+</div>
                <div class="stat-label">Economic Indicators</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">10yr</div>
                <div class="stat-label">Seasonality Data</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="contact-section">
        <h2 class="contact-title">Ready to Upgrade Your Trading?</h2>
        <p class="contact-subtitle">Join professional traders using MacroPulse to gain a true edge in the forex market.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("Get Started Now", key="btn_get_started"):
            st.session_state.show_auth = True
            st.rerun()

    st.markdown("""
    <div class="footer">
        <p>&copy; 2024 MacroPulse Analytics. All rights reserved.</p>
        <p><a href="#" style="color: #64748b; text-decoration: none;">Privacy Policy</a> | <a href="#" style="color: #64748b; text-decoration: none;">Terms of Service</a></p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">Forex trading involves substantial risk. Past performance does not guarantee future results.</p>
    </div>
    """, unsafe_allow_html=True)


def show_auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-header">
            <h2>MacroPulse</h2>
            <p>Access the Intelligence Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.auth_mode == "login":
            st.markdown("<h3 style='text-align: center; color: white;'>Log In</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log In", use_container_width=True)
                
                if submitted:
                    success, msg = sign_in(email.strip(), password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.show_auth = False
                        st.success("Login successful! Redirecting...")
                        time.sleep(0.5) 
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("<div class='toggle-btn-container'>", unsafe_allow_html=True)
            if st.button("Need an account? Register here", key="switch_to_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown("<h3 style='text-align: center; color: white;'>Register</h3>", unsafe_allow_html=True)
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
                submitted = st.form_submit_button("Register", use_container_width=True)
                
                if submitted:
                    if new_password != confirm:
                        st.error("Passwords do not match")
                    else:
                        success, msg = sign_up(new_email, new_password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                            
            st.markdown("<div class='toggle-btn-container'>", unsafe_allow_html=True)
            if st.button("← Back to Login", key="switch_to_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.show_auth = False
            st.session_state.auth_mode = "login"
            st.rerun()

# ======================= MAIN APP ROUTING =======================
if not st.session_state.authenticated:
    if st.session_state.show_auth:
        show_auth_page()
    else:
        show_landing_page()
    st.stop()

# --- IF AUTHENTICATED ---
try:
    st.switch_page("pages/01_Top_Setups.py")
except Exception as e:
    st.error("🚨 Navigation Error: Streamlit could not find the file 'pages/1_top_setups.py'.")
    st.warning("Please check your 'pages' folder and ensure the file is named exactly '1_top_setups.py'.")
