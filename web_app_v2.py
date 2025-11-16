"""
Supply Chain AI Chatbot - Main Application
Landing Page
"""
import streamlit as st
from pathlib import Path
import sys
import base64

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.helpers import load_css
from components.ui_components import (
    render_header, 
    render_feature_card, render_step_card
)

# Page configuration
st.set_page_config(
    page_title="Supply Chain AI - Home",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Prevent downstream code (e.g., exec(app_v8.py)) from calling set_page_config again
def _st_page_config_noop(*args, **kwargs):
    return None
st.set_page_config = _st_page_config_noop

# Layout and chrome tweaks (keep sidebar visible)
st.markdown("""
    <style>
        /* Hide only the default top menu and footer */
        header[data-testid="stHeader"] {display: none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Make main content a bit wider while preserving scroll and sidebar */
        [data-testid="stAppViewContainer"] > .main > div {
            max-width: 1300px;
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Load custom CSS
load_css()

# Load images as base64
def load_image_as_base64(image_path):
    """Load image and convert to base64"""
    from pathlib import Path
    p = Path(image_path)

    def read_if_exists(path: Path):
        if path.exists():
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return None

    # 1) Direct path, relative to CWD
    data = read_if_exists(p)
    if data:
        return data

    # 2) Relative to BASE_DIR
    data = read_if_exists(BASE_DIR / p)
    if data:
        return data

    # 3) Inside BASE_DIR/images using provided filename
    data = read_if_exists(BASE_DIR / "images" / p.name)
    if data:
        return data

    # 4) Case-insensitive/ext-insensitive search by stem in common locations
    search_dirs = [BASE_DIR, BASE_DIR / "images"]
    stems = {p.stem, p.name}  # consider both stem and full name
    exts = [".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG", ".webp", ".WEBP"]
    for d in search_dirs:
        for stem in stems:
            for ext in exts:
                candidate = d / f"{Path(stem).stem}{ext}"
                data = read_if_exists(candidate)
                if data:
                    return data

    # If not found, raise a clear error with searched locations
    tried = [
        str(p),
        str(BASE_DIR / p),
        str(BASE_DIR / "images" / p.name),
        "and multiple case/extension variants in BASE_DIR and BASE_DIR/images"
    ]
    raise FileNotFoundError(f"Image not found. Tried: {', '.join(tried)}")

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'


def render_hero_with_bg():
    """Render hero section with background image and centered logo"""
    # Load images
    bg_image = load_image_as_base64('images/hero-bg.jpg')
    logo_image = load_image_as_base64('images/logo.png')
    
    st.markdown(f"""
        <style>
        .hero-with-bg {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url(data:image/jpeg;base64,{bg_image});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            padding: 150px 20px;
            border-radius: 0px;
            text-align: center;
            color: white;
            position: relative;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: -80px 0 0 0;
            width: 100vw;
            margin-left: calc(-50vw + 50%);
        }}
        
        .hero-logo {{
            width: 150px;
            height: 150px;
            margin-bottom: 15px;
            border-radius: 50%;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        }}
        
        .hero-brand {{
            font-size: 40px;
            font-weight: 700;
            color: white;
            margin-bottom: 15px;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.6);
        }}
        
        .hero-title {{
            font-size: clamp(34px, 6vw, 52px);
            font-weight: 700;
            color: white;
            margin-bottom: 20px;
            line-height: 1.1;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.6);
        }}
        
        .hero-subtitle {{
            font-size: clamp(14px, 3vw, 18px);
            color: rgba(255, 255, 255, 0.95);
            max-width: 900px;
            margin: 0 auto 40px auto;
            line-height: 1.6;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
        }}
        </style>
        
        <div class="hero-with-bg">
            <img src="data:image/png;base64,{logo_image}" class="hero-logo" alt="InsightFlow AI Logo">
            <div class="hero-brand">InsightFlow AI</div>
            <h1 class="hero-title">
                Supply Chain Data Analytics<br>
                <span style="color: #00d4ff;">Powered by AI</span>
            </h1>
            <p class="hero-subtitle">
                Smart platform to help you understand your data deeper and predict future trends<br>
                through simple conversation with AI
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Add buttons inside hero section
    st.markdown("<div style='margin-top: -80px; position: relative; z-index: 10;'>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 0.3, 1, 1.5])
    with col2:
        if st.button("🚀 Get Started Free", use_container_width=True, type="primary", key="hero_signup"):
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'signup'
            st.rerun()
    with col4:
        if st.button("Login", use_container_width=True, key="hero_login"):
            st.session_state.page = 'auth'
            st.session_state.auth_mode = 'login'
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def landing_page():
    """Render landing page"""
    # Hide sidebar on landing page (clean, full-width hero)
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # Hero Section with Background (Full Screen)
    render_hero_with_bg()
    
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
            <p style="margin: 0;">&copy; 2024 InsightFlow AI. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)


# Main app
if __name__ == "__main__":
    # Check what page to show
    if st.session_state.user is not None:
        # User is logged in, show chat page with sidebar
        # Update page config for chat (needs sidebar)
        st.markdown("""
            <style>
                [data-testid="stSidebarNav"] {display: none;}
            </style>
        """, unsafe_allow_html=True)
        # Use the stable chat page implementation to avoid nested chat_input issues
        #exec(open('pages/chat_page.py', encoding='utf-8').read())
        with open('app_v8.py', encoding='utf-8') as f:
                exec(f.read())
    elif st.session_state.page == 'auth':
        # Show auth page (no sidebar)
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {display: none;}
                section[data-testid="stSidebar"] {display: none;}
            </style>
        """, unsafe_allow_html=True)
        # Prefer new auth page file if present; fallback not needed here
        exec(open('pages/auth_page_v2.py', encoding='utf-8').read())
    else:
        # Show landing page (no sidebar)
        landing_page()