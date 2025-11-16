# app.py (Updated)
import base64
import importlib
from pathlib import Path
import sys

import streamlit as st


BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))


def get_img_base64(path: Path) -> str:
    img_bytes = path.read_bytes()
    return base64.b64encode(img_bytes).decode()


LOGO_BASE64 = get_img_base64(BASE_DIR / "images/logo2.png")

from utils.helpers import load_css
from pages.auth_page_v2 import render_auth_page
from components.ui_components import (
    render_header,
    render_hero_section,
    render_feature_card,
    render_step_card,
)

# Page configuration
if not st.session_state.get("_main_page_config_set", False):
    st.set_page_config(
        page_title="Supply Chain AI - Home",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.session_state["_main_page_config_set"] = True

# Load custom CSS
load_css()

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'


def set_sidebar_visibility(visible: bool) -> None:
    """Toggle sidebar visibility via CSS."""
    if visible:
        css = """
        <style>
            [data-testid="stSidebar"] {
                display: block !important;
                visibility: visible !important;
                min-width: 400px !important;
                width: 400px !important;
            }
            section[data-testid="stSidebar"] {
                display: block !important;
                visibility: visible !important;
                min-width: 400px !important;
                width: 400px !important;
            }
            [data-testid="stSidebar"] > div {
                min-width: 400px !important;
                width: 400px !important;
            }
            [data-testid="stSidebarNav"] {
                display: none !important;
                visibility: hidden !important;
            }
            [data-testid="stSidebar"][aria-expanded="true"] {
                display: block !important;
                visibility: visible !important;
                min-width: 400px !important;
                width: 400px !important;
            }
            button[data-testid="baseButton-header"] {
                display: block !important;
            }
        </style>
        """
    else:
        css = """
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            section[data-testid="stSidebar"] {display: none !important;}
            [data-testid="stSidebarNav"] {display: none !important;}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

def landing_page():
    """Render landing page"""
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:16px;padding:16px;">
    <div style="width:140px;height:140px;background:linear-gradient(135deg,#0073e6 0%,#004280 100%);border-radius:32px;display:flex;align-items:center;justify-content:center;">
        <img src="data:image/jpeg;base64,{LOGO_BASE64}"
            style="width:115px;height:115px;object-fit:contain;border-radius:24px;" />
    </div>
    <div style="margin:0;color:#111827;font-size:28px;font-weight:600;">
        InsightFlow AI
    </div>
    </div>""",
            unsafe_allow_html=True,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hero Section
    render_hero_section()
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 Get Started Free", use_container_width=True, type="primary"):
                st.session_state.page = 'auth'
                st.session_state.auth_mode = 'signup'
                st.rerun()
        with col_b:
            if st.button("Already have an account?", use_container_width=True):
                st.session_state.page = 'auth'
                st.session_state.auth_mode = 'login'
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown("""
        <div style="background: white; padding: 60px 20px; border-radius: 16px; margin: 40px 0;">
            <h2 style="text-align: center; color: #111827; margin-bottom: 16px;">
                How It Works?
            </h2>
            <p style="text-align: center; color: #6b7280; font-size: 18px; margin-bottom: 48px;">
                Three simple steps to get comprehensive analysis of your data
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_step_card(
            "1", "✓",
            "Sign Up or Login",
            "Quick and secure account creation in less than a minute"
        )
    
    with col2:
        render_step_card(
            "2", "📤",
            "Upload Your Data",
            "Upload a CSV or Excel file containing your supply chain data"
        )
    
    with col3:
        render_step_card(
            "3", "💬",
            "Chat with AI",
            "Request analysis or forecasting and get instant results with charts"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Features Section
    st.markdown("""
        <div style="padding: 60px 20px;">
            <h2 style="text-align: center; color: #111827; margin-bottom: 16px;">
                Key Features
            </h2>
            <p style="text-align: center; color: #6b7280; font-size: 18px; margin-bottom: 48px;">
                Everything you need to manage and analyze your supply chain
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_feature_card(
            "📊",
            "Comprehensive Data Analysis",
            "Get in-depth analysis of your data with interactive charts and accurate statistics"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        render_feature_card(
            "💬",
            "Interactive Conversation",
            "Communicate with the system in natural language and get instant answers to all your questions"
        )
    
    with col2:
        render_feature_card(
            "🤖",
            "AI-Powered Accurate Predictions",
            "Forecast future sales, revenue, and prices using advanced models"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        render_feature_card(
            "📤",
            "Multiple File Support",
            "Easily upload CSV and Excel files and start analysis immediately"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0073e6 0%, #005bb3 100%); 
             padding: 60px 20px; border-radius: 16px; text-align: center; color: white; margin: 40px 0;">
            <h2 style="color: white; margin-bottom: 16px; font-size: clamp(24px, 5vw, 36px);">Ready to Get Started?</h2>
            <p style="font-size: clamp(14px, 3vw, 18px); opacity: 0.9; margin-bottom: 32px; max-width: 800px; margin-left: auto; margin-right: auto;">
                Join hundreds of companies using AI to improve their supply chain
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Now - Free", use_container_width=True, type="primary", key="cta_button"):
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signup'
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style="background: #111827; padding: 20px; text-align: center; color: #9ca3af; 
             border-radius: 8px; margin-top: 60px;">
            <p style="margin: 0;">&copy; 2024 Supply Chain AI. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

# # Main app
# if __name__ == "__main__":
#     # Check what page to show
#     if st.session_state.user is not None:
#         # User is logged in - show the main forecasting app
#         # Remove the sidebar hiding for logged-in users
#         st.markdown("""
#             <style>
#                 [data-testid="stSidebarNav"] {display: none;}
#             </style>
#         """, unsafe_allow_html=True)
        
#         # Import and run your main chat app
#         try:
#             # Import your main chat functionality
#             import sys
#             sys.path.append(str(Path(__file__).parent))
            
#             # Run your main chat app
#             exec(open('app_v8.py').read())
            
#         except Exception as e:
#             st.error(f"Error loading chat application: {e}")
#             st.info("Please ensure app_v8.py is in the same directory")
            
#     elif st.session_state.page == 'auth':
#         # Show auth page (no sidebar)
#         st.markdown("""
#             <style>
#                 [data-testid="stSidebar"] {display: none;}
#                 section[data-testid="stSidebar"] {display: none;}
#             </style>
#         """, unsafe_allow_html=True)
#         render_auth_page()
#     else:
#         # Show landing page (no sidebar)
#         landing_page()
# Main app controller
if __name__ == "__main__":
    # Check what page to show
    if st.session_state.user is not None:
        # User is logged in - show the main forecasting app
        # Set sidebar visibility BEFORE importing the app
        set_sidebar_visibility(True)
        
        # Also add inline CSS and JavaScript to ensure sidebar is visible and open
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    display: block !important;
                    visibility: visible !important;
                    transform: translateX(0) !important;
                    min-width: 400px !important;
                    width: 400px !important;
                }
                section[data-testid="stSidebar"] {
                    display: block !important;
                    visibility: visible !important;
                    transform: translateX(0) !important;
                    min-width: 400px !important;
                    width: 400px !important;
                }
                [data-testid="stSidebar"] > div {
                    min-width: 400px !important;
                    width: 400px !important;
                }
                [data-testid="stSidebarNav"] {
                    display: none !important;
                    visibility: hidden !important;
                }
                button[aria-label*="sidebar"],
                button[aria-label*="menu"],
                button[data-testid="baseButton-header"] {
                    display: block !important;
                }
            </style>
            <script>
                function forceOpenSidebar() {
                    // Find sidebar
                    const sidebar = document.querySelector('[data-testid="stSidebar"]');
                    const sidebarSection = document.querySelector('section[data-testid="stSidebar"]');
                    
                    // Find sidebar toggle button
                    const buttons = document.querySelectorAll('button[data-testid="baseButton-header"]');
                    let sidebarButton = null;
                    buttons.forEach(btn => {
                        const label = btn.getAttribute('aria-label') || '';
                        if (label.toLowerCase().includes('sidebar') || label.toLowerCase().includes('menu') || label.toLowerCase().includes('open')) {
                            sidebarButton = btn;
                        }
                    });
                    
                    if (sidebar || sidebarSection) {
                        const target = sidebar || sidebarSection;
                        target.style.display = 'block';
                        target.style.visibility = 'visible';
                        target.style.transform = 'translateX(0)';
                        target.setAttribute('aria-expanded', 'true');
                    }
                    
                    // Click the sidebar button if it exists
                    if (sidebarButton) {
                        sidebarButton.click();
                    }
                }
                
                // Run immediately and on intervals
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', forceOpenSidebar);
                } else {
                    forceOpenSidebar();
                }
                
                setTimeout(forceOpenSidebar, 100);
                setTimeout(forceOpenSidebar, 500);
                setTimeout(forceOpenSidebar, 1000);
                setTimeout(forceOpenSidebar, 2000);
            </script>
        """, unsafe_allow_html=True)

        # Import and run the main chat app
        try:
            # Use exec to directly execute app_v8.py
            # This ensures all code including sidebar executes in the right context
            app_v8_path = BASE_DIR / "app_v8.py"
            
            if app_v8_path.exists():
                # Allow app_v8 to set its page config (including initial_sidebar_state)
                # Only if it hasn't been set yet
                if "_app_v8_executed" not in st.session_state:
                    st.session_state["_main_page_config_set"] = False
                    st.session_state["_app_v8_executed"] = True
                
                # Read and execute the file directly
                with open(app_v8_path, 'r', encoding='utf-8') as f:
                    app_v8_code = f.read()
                
                # Execute the code - this will run the sidebar code and page config
                exec(app_v8_code, globals())
            else:
                st.error(f"app_v8.py not found at {app_v8_path}")

        except Exception as e:
            st.error(f"Error loading chat application: {e}")
            st.info("Please ensure app_v8.py is in the same directory")
            import traceback
            st.code(traceback.format_exc())
            
    elif st.session_state.page == 'auth':
        # Show auth page (no sidebar)
        set_sidebar_visibility(False)
        render_auth_page()
    else:
        # Show landing page (no sidebar)
        set_sidebar_visibility(False)
        landing_page()


