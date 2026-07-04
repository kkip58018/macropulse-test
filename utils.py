import streamlit as st
import yfinance as yf
import pandas as pd
import glob
from db import supabase_auth, supabase_admin, save_session,get_session_file
from datetime import datetime, timedelta
from pathlib import Path
from config import FOREX_PAIRS, CORE_INDICATORS, SCORING_ONLY_INDICATORS, EXTRA_INDICATORS, SCORING_EXCLUDED_INDICATORS, DIRECTION


# ======================= AUTHENTICATION LOGIC =======================
def sign_in(email, password):
    try:
        response = supabase_auth.auth.sign_in_with_password({"email": email, "password": password})
        if response and response.session:
            user_id = response.user.id
            profile = supabase_admin.table("user_profiles").select("approved, is_admin").eq("id", user_id).execute()
            if profile.data:
                if not profile.data[0].get("approved", False):
                    supabase_auth.auth.sign_out()
                    return False, "Account pending approval. Please contact an admin."
                if profile.data[0].get("is_admin", False):
                    st.session_state.is_admin = True
            else:
                return False, "User profile not found in database."
            save_session(response.session, email)
            st.session_state.authenticated = True
            st.query_params["auth"] = "true"
            # We no longer switch page; we just stay on the main app
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
    
def sign_out():
    try:
        supabase_auth.auth.sign_out()
    except:
        pass
    # Delete the session file for the current user
    if st.session_state.get("user_email"):
        file_path = get_session_file(st.session_state.user_email)
        file_path.unlink(missing_ok=True)
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.is_admin = False
    st.session_state.show_auth = False
    st.rerun()




def normalize_pair(pair_str):
    """Convert any pair like 'GBP/EUR' to the standard format in FOREX_PAIRS."""
    pair_str = pair_str.upper().replace(" ", "")
    if pair_str in FOREX_PAIRS:
        return pair_str
    # Try reverse
    parts = pair_str.split("/")
    if len(parts) == 2:
        reversed_pair = f"{parts[1]}/{parts[0]}"
        if reversed_pair in FOREX_PAIRS:
            return reversed_pair
    # Fallback: return as-is
    return pair_str


# ======================= SEASONALITY HELPERS =======================
def get_yf_symbol(pair: str) -> str:
    """Map a trading pair to a yfinance ticker symbol."""
    pair = pair.upper()
    if pair == "XAU/USD":
        return "GC=F"
    if pair == "XAG/USD":
        return "SI=F"
    if pair == "BTC/USD":
        return "BTC-USD"
    if pair == "ETH/USD":
        return "ETH-USD"
    if pair == "USOIL/USD":
        return "CL=F"
    if pair == "SPX500/USD":
        return "^GSPC"
    if pair == "NAS100/USD":
        return "^IXIC"
    # Forex: e.g. "EUR/USD" -> "EURUSD=X"
    base, quote = pair.split("/")
    return f"{base}{quote}=X"

def get_base_quote(c1, c2):
    priority = ["GBP", "EUR", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"]
    try:
        i1 = priority.index(c1)
    except ValueError:
        i1 = 999
    try:
        i2 = priority.index(c2)
    except ValueError:
        i2 = 999
    return (c1, c2) if i1 < i2 else (c2, c1)


def format_date_dd_mon(date_val):
    if date_val is None:
        return "N/A"
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.strftime("%d-%b")
    if isinstance(date_val, str):
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d-%b"]:
            try:
                dt = datetime.strptime(date_val, fmt)
                return dt.strftime("%d-%b")
            except:
                continue
        return date_val
    return str(date_val)


def get_sort_key_dd_mon(date_str):
    if date_str == "N/A":
        return (99, 99)
    try:
        dt = datetime.strptime(date_str + "-2025", "%d-%b-%Y")
        return (dt.month, dt.day)
    except:
        return (99, 99)

def determine_outcome(actual, forecast, direction):
    if direction == "higher":
        if actual > forecast:
            return "beat"
        elif actual == forecast:
            return "expected"
        else:
            return "lower"
    else:
        if actual < forecast:
            return "beat"
        elif actual == forecast:
            return "expected"
        else:
            return "lower"
        
# ======================= DATA LOADING =======================
def load_currency_data(file_path: str) -> dict:
    df = pd.read_excel(file_path)
    df["Indicator"] = df["Indicator"].str.strip()
    data = {}
    has_date = "Date" in df.columns
    has_prev = "Previous" in df.columns
    for _, row in df.iterrows():
        ind = row["Indicator"]
        actual = pd.to_numeric(row["Actual"], errors="coerce")
        forecast = pd.to_numeric(row["Forecast"], errors="coerce")
        if pd.isna(actual) or pd.isna(forecast):
            continue
        date_val = row["Date"] if has_date else None
        prev_val = pd.to_numeric(row["Previous"], errors="coerce") if has_prev else None
        data[ind] = (actual, forecast, date_val, prev_val)
    return data


def load_all_currencies(data_folder: str) -> dict:
    files = glob.glob(str(Path(data_folder) / "*.xlsx"))
    currencies = {}
    for f in files:
        code = Path(f).stem.upper()
        currencies[code] = load_currency_data(f)
    return currencies


def compute_bullish_percentage(currency_data: dict, currency_code: str) -> float:
    indicators = list(CORE_INDICATORS) + list(SCORING_ONLY_INDICATORS)
    if currency_code in EXTRA_INDICATORS:
        indicators.extend(EXTRA_INDICATORS[currency_code])
    if currency_code in SCORING_EXCLUDED_INDICATORS:
        for excl in SCORING_EXCLUDED_INDICATORS[currency_code]:
            if excl in indicators:
                indicators.remove(excl)
    beats = 0
    surprises = 0
    for ind in indicators:
        if ind not in currency_data:
            continue
        actual, forecast, _, _ = currency_data[ind]
        direction = DIRECTION.get(ind)
        if direction is None:
            continue
        if actual == forecast:
            continue
        surprises += 1
        if (direction == "higher" and actual > forecast) or (
            direction == "lower" and actual < forecast
        ):
            beats += 1
    return (beats / surprises) * 100.0 if surprises > 0 else 0.0

@st.cache_data(ttl=86400, show_spinner=False)
def load_seasonality_data(pair: str):
    """Fetch 10 years of daily OHLC data for the given pair."""
    symbol = get_yf_symbol(pair)
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="10y", interval="1d")
    if df.empty:
        return None
    df.index = pd.to_datetime(df.index)
    return df

def get_kenyan_time_str():
        # Server is usually UTC. EAT is UTC+3.
        return (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S EAT")


