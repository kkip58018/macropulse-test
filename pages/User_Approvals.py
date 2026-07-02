import streamlit as st
import pandas as pd
from db import supabase_admin
from analyzer import init_analyzer 
from config import *

if not st.session_state.get("authenticated", False):
    st.warning("Please log in on the Home page first.")
    st.stop()

analyzer = init_analyzer()


st.header("👥 User Approvals")
st.markdown("Approve pending user accounts.")
try:
    resp = (
        supabase_admin.table("user_profiles")
        .select("*")
        .order("created_at", desc=False)
        .execute()
    )
    profiles = resp.data
    pending = [p for p in profiles if not p.get("approved", False)]
    approved = [p for p in profiles if p.get("approved", False)]
    tab_pending, tab_approved = st.tabs(
        ["⏳ Pending Approval", "✅ Approved Users"]
    )
    with tab_pending:
        if pending:
            df_pending = pd.DataFrame(pending)
            cols = ["email", "created_at"]
            display_cols = [c for c in cols if c in df_pending.columns]
            st.dataframe(
                df_pending[display_cols], use_container_width=True, hide_index=True
            )
            st.markdown("### Approve User")
            email_to_approve = st.selectbox(
                "Select email", [p["email"] for p in pending]
            )
            if st.button("Approve Selected User"):
                user = next(
                    (p for p in pending if p["email"] == email_to_approve), None
                )
                if user:
                    supabase_admin.table("user_profiles").update(
                        {"approved": True}
                    ).eq("id", user["id"]).execute()
                    st.session_state.success_msg = (
                        f"User {email_to_approve} approved successfully."
                    )
                    st.rerun()
        else:
            st.info("No pending approvals.")
    with tab_approved:
        if approved:
            df_approved = pd.DataFrame(approved)
            cols = ["email", "is_admin", "created_at"]
            display_cols = [c for c in cols if c in df_approved.columns]
            st.dataframe(
                df_approved[display_cols], use_container_width=True, hide_index=True
            )
        else:
            st.info("No approved users.")
except Exception as e:
    st.error(f"Error fetching user profiles: {e}")
