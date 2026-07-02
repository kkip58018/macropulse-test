import streamlit as st
import time
from db import supabase_auth, supabase_admin, save_session
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

# ======================= GLOBAL STYLES =======================
# Base CSS that applies everywhere
base_css = """
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

    /* Hero / Auth custom styles */
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin-top: 10vh;
        background: linear-gradient(90deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
    }
    .auth-container {
        background-color: #1e2430;
        padding: 2rem;
        border-radius: 10px;
        max-width: 400px;
        margin: 0 auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #2a3340;
    }
    .toggle-btn-container {
        text-align: center;
        margin-top: 1rem;
    }
</style>
"""
st.markdown(base_css, unsafe_allow_html=True)

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
            save_session(response.session, email)
            
            # Check admin and approval status
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
    st.markdown("<div class='hero-title'>MacroPulse</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Institutional-Grade Macroeconomic Intelligence</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("Enter Dashboard", use_container_width=True, type="primary"):
            st.session_state.show_auth = True
            st.rerun()

def show_auth_page():
    st.markdown("<div class='hero-title'>MacroPulse</div>", unsafe_allow_html=True)
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    if st.session_state.auth_mode == "login":
        st.markdown("<h3 style='text-align: center; color: white;'>Log In</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
            
            if submitted:
                success, msg = sign_in(email, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.show_auth = False
                    st.success("Loading your dashboard....")
                    time.sleep(0.5) # Give the user half a second to read the success message
                    
                    # 🚀 REDIRECT DIRECTLY TO TOP SETUPS PAGE
                    st.switch_page("pages/top_setups.py")
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

    st.markdown("</div>", unsafe_allow_html=True)
    
    # Back to Home button (outside the card)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
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

st.switch_page("pages/top_setups.py")
