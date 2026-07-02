from supabase import create_client, Client
import streamlit as st
import json
from pathlib import Path

# ======================= SUPABASE CONFIG =======================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ======================= SESSION PERSISTENCE =======================
def get_session_file(email: str) -> Path:
    """Create a safe filename from the user's email."""
    safe_email = email.replace("@", "_at_").replace(".", "_")
    return Path.cwd() / f".supabase_session_{safe_email}.json"


def save_session(session, email: str):
    """Save the session tokens to the user's personal file."""
    try:
        data = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at,
            "email": email,
        }
        file_path = get_session_file(email)
        with open(file_path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass  # Silently fail if file can't be written


def load_session(email: str) -> bool:
    """
    Try to restore a session from the user's personal file.
    Returns True if successful and user is still approved.
    """
    try:
        file_path = get_session_file(email)
        if not file_path.exists():
            return False
        with open(file_path, "r") as f:
            data = json.load(f)
        # Security check: stored email must match the one we're trying to load
        if data.get("email") != email:
            return False
        # Restore the session in Supabase
        supabase_auth.auth.set_session(data["access_token"], data["refresh_token"])
        session = supabase_auth.auth.get_session()
        if session and session.user:
            user_id = session.user.id
            profile = (
                supabase_admin.table("user_profiles")
                .select("approved, is_admin")
                .eq("id", user_id)
                .execute()
            )
            if profile.data and profile.data[0].get("approved", False):
                return True
        # If anything fails, delete the invalid file
        file_path.unlink(missing_ok=True)
        return False
    except Exception:
        return False
