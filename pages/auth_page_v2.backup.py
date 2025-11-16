"""
auth_page_v2.py
Streamlit authentication (login & signup) experience for web_app_v2.
"""

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from utils.helpers import (
    load_css,
    login_user,
    register_user,
    validate_email,
    validate_password,
)


def _init_state() -> None:
    """Ensure required keys exist in st.session_state."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"


def login_form() -> None:
    """Render login form."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <h2 style="text-align: center; color: #111827; margin-bottom: 8px;">Welcome Back</h2>
        <p style="text-align: center; color: #6b7280; margin-bottom: 24px;">
            Log in to access your account
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form_v2"):
        email = st.text_input(
            "📧 Email Address",
            placeholder="example@email.com",
            key="login_email_v2",
        )
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="••••••••",
            key="login_password_v2",
        )

        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Remember me", key="login_remember_v2")
        with col2:
            st.markdown(
                """
                <div style="text-align: right; padding-top: 8px;">
                    <a href="#" style="color: #0073e6; text-decoration: none; font-size: 14px;">
                        Forgot password?
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )

        submit = st.form_submit_button(
            "Login", use_container_width=True, type="primary"
        )

    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
        elif not validate_email(email):
            st.error("Invalid email format")
        else:
            success, result = login_user(email, password)
            if success:
                st.session_state.user = {
                    "email": email,
                    "name": result["name"],
                }
                st.success("Login successful! Loading AI Chat...")
                st.balloons()
                st.rerun()
            else:
                st.error(result)


def signup_form() -> None:
    """Render signup form."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <h2 style="text-align: center; color: #111827; margin-bottom: 8px;">Create New Account</h2>
        <p style="text-align: center; color: #6b7280; margin-bottom: 24px;">
            Start your data analytics journey
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form_v2"):
        name = st.text_input(
            "👤 Full Name",
            placeholder="Enter your full name",
            key="signup_name_v2",
        )
        email = st.text_input(
            "📧 Email Address",
            placeholder="example@email.com",
            key="signup_email_v2",
        )
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="••••••••",
            help="Password must be at least 6 characters long",
            key="signup_password_v2",
        )
        confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            placeholder="••••••••",
            key="signup_confirm_v2",
        )
        terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            key="signup_terms_v2",
        )

        submit = st.form_submit_button(
            "Create Account", use_container_width=True, type="primary"
        )

    if submit:
        if not all([name, email, password, confirm_password]):
            st.error("Please fill in all fields")
        elif not validate_email(email):
            st.error("Invalid email format")
        elif password != confirm_password:
            st.error("Passwords do not match")
        else:
            valid, message = validate_password(password)
            if not valid:
                st.error(message)
            elif not terms:
                st.error("Please agree to the Terms of Service")
            else:
                success, result = register_user(name, email, password)
                if success:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(result)


def render_auth_page() -> None:
    """Render the full authentication experience."""
    load_css()
    _init_state()

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #0073e6 0%, #004280 100%);
                        border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;
                        margin-bottom: 16px;">
                <img src="logo_scai.jpg" style="width: 36px; height: 36px; object-fit: contain; border-radius: 8px;" />
            </div>
            <h1 style="color: #111827; margin-bottom: 8px;">Supply Chain AI</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["🔑 Login", "✨ Sign Up"])
    if st.session_state.auth_mode == "signup":
        with tabs[1]:
            signup_form()
        with tabs[0]:
            login_form()
    else:
        with tabs[0]:
            login_form()
        with tabs[1]:
            signup_form()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True, key="back_home_v2"):
            st.session_state.page = "landing"
            st.session_state.auth_mode = "login"
            st.rerun()


if __name__ == "__main__":
    render_auth_page()