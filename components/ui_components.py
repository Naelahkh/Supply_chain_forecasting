"""
Reusable UI components for Supply Chain AI Chatbot
"""
import streamlit as st
from datetime import datetime


def render_top_navbar(show_auth_buttons: bool = False):
    """Render top navigation bar with logo (and optional auth buttons)"""
    # نجهز HTML للأزرار إذا نحتاج نعرضها
    auth_buttons_html = ""
    if show_auth_buttons:
        auth_buttons_html = """
            <div class="navbar-actions">
                <a class="nav-btn nav-btn-outline" href="/?page=auth&mode=login">
                    Login
                </a>
                <a class="nav-btn nav-btn-primary" href="/?page=auth&mode=signup">
                    Get started
                </a>
            </div>
        """

    st.markdown(f"""
        <style>
        .top-navbar {{
            background: #1f2937;
            padding: 12px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }}
        
        .navbar-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            font-size: 20px;
            font-weight: 600;
        }}

        .navbar-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .nav-btn {{
            padding: 6px 16px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            border: 1px solid transparent;
        }}

        .nav-btn-primary {{
            background: #0073e6;
            color: white;
            border-color: #0073e6;
        }}

        .nav-btn-outline {{
            background: transparent;
            color: white;
            border-color: #9ca3af;
        }}

        .nav-btn-primary:hover {{
            background: #005bb5;
            border-color: #005bb5;
        }}

        .nav-btn-outline:hover {{
            background: rgba(255,255,255,0.08);
        }}

        /* ممكن تعدلين البادينق حسب ما تحبين */
        .main .block-container {{
            padding-top: 0px !important;
        }}
        </style>
        
        <div class="top-navbar">
            <div class="navbar-brand">
                <span style="font-size: 28px;">🤖</span>
                <span>InsightFlow AI</span>
            </div>
            {auth_buttons_html}
        </div>
    """, unsafe_allow_html=True)



def render_header(title, show_logout=False):
    """Render custom header"""
    st.markdown(f"""
        <div class="custom-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #0073e6 0%, #004280 100%); 
                         border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 24px;">🤖</span>
                    </div>
                    <h2 style="margin: 0; color: #111827;">Supply Chain AI</h2>
                </div>
                <h3 style="margin: 0; color: #6b7280;">{title}</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_hero_section():
    """Render hero section for landing page"""
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">
                Supply Chain Data Analytics<br>
                <span style="color: #0073e6;">Powered by AI</span>
            </h1>
            <p class="hero-subtitle">
                Smart platform to help you understand your data deeper and predict future trends<br>
                through simple conversation with AI
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_feature_card(icon, title, description):
    """Render a feature card"""
    st.markdown(f"""
        <div class="feature-card">
            <div style="font-size: 48px; margin-bottom: 16px;">{icon}</div>
            <h3 style="color: #111827; margin-bottom: 12px;">{title}</h3>
            <p style="color: #6b7280; font-size: 14px;">{description}</p>
        </div>
    """, unsafe_allow_html=True)


def render_step_card(number, icon, title, description):
    """Render a step card"""
    st.markdown(f"""
        <div class="step-card">
            <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">{icon}</div>
            <div class="step-number">{number}</div>
            <h3 style="color: #111827; margin-bottom: 8px;">{title}</h3>
            <p style="color: #6b7280; font-size: 14px;">{description}</p>
        </div>
    """, unsafe_allow_html=True)


def render_chat_message(message, is_user=True):
    """Render a chat message"""
    avatar = "👤" if is_user else "🤖"
    bg_color = "white" if is_user else "#0073e6"
    text_color = "#111827" if is_user else "white"
    border = "1px solid #e5e7eb" if is_user else "none"
    align = "flex-start" if is_user else "flex-end"
    
    timestamp = datetime.fromisoformat(message['timestamp']).strftime("%I:%M %p")
    
    st.markdown(f"""
        <div style="display: flex; justify-content: {align}; margin: 12px 0;">
            <div style="background: {bg_color}; color: {text_color}; 
                 border: {border}; border-radius: 12px; padding: 16px; 
                 max-width: 70%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="font-size: 20px;">{avatar}</span>
                    <strong>{"You" if is_user else "AI Assistant"}</strong>
                    <span style="font-size: 12px; opacity: 0.7;">{timestamp}</span>
                </div>
                <div style="white-space: pre-wrap;">{message['content']}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar_chat_item(chat, is_active=False):
    """Render a chat item in sidebar"""
    border = "2px solid #0073e6" if is_active else "1px solid #e5e7eb"
    bg = "#e6f2ff" if is_active else "white"
    
    created_at = datetime.fromisoformat(chat['created_at'])
    time_str = format_time_ago(created_at)
    
    st.markdown(f"""
        <div style="background: {bg}; border: {border}; border-radius: 8px; 
             padding: 12px; margin: 8px 0; cursor: pointer;">
            <div style="font-weight: 600; color: #111827; margin-bottom: 4px;">
                {chat['title'][:30]}{"..." if len(chat['title']) > 30 else ""}
            </div>
            <div style="font-size: 12px; color: #6b7280;">
                {time_str} • {len(chat['messages'])} messages
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_quick_action_button(label, emoji):
    """Render a quick action button"""
    st.markdown(f"""
        <style>
        .quick-action {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            margin: 4px;
        }}
        .quick-action:hover {{
            background: #e6f2ff;
            border-color: #0073e6;
        }}
        </style>
        <span class="quick-action">{emoji} {label}</span>
    """, unsafe_allow_html=True)


def render_stat_card(label, value, icon, color="#0073e6"):
    """Render a statistics card"""
    st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 20px; 
             box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
            <div style="font-size: 36px; margin-bottom: 8px;">{icon}</div>
            <div style="font-size: 28px; font-weight: bold; color: {color}; margin-bottom: 4px;">
                {value}
            </div>
            <div style="font-size: 14px; color: #6b7280;">{label}</div>
        </div>
    """, unsafe_allow_html=True)


def render_info_box(message, type="info"):
    """Render an info/success/error box"""
    colors = {
        'info': {'bg': '#dbeafe', 'border': '#3b82f6', 'text': '#1e40af'},
        'success': {'bg': '#d1fae5', 'border': '#10b981', 'text': '#065f46'},
        'error': {'bg': '#fee2e2', 'border': '#ef4444', 'text': '#991b1b'},
        'warning': {'bg': '#fef3c7', 'border': '#f59e0b', 'text': '#92400e'}
    }
    
    style = colors.get(type, colors['info'])
    
    st.markdown(f"""
        <div style="background: {style['bg']}; border: 1px solid {style['border']}; 
             border-radius: 8px; padding: 12px; color: {style['text']};">
            {message}
        </div>
    """, unsafe_allow_html=True)


def render_file_upload_area():
    """Render file upload area"""
    st.markdown("""
        <div style="border: 2px dashed #0073e6; border-radius: 12px; 
             padding: 40px; text-align: center; background: #e6f2ff;">
            <div style="font-size: 48px; margin-bottom: 16px;">📤</div>
            <h3 style="color: #111827; margin-bottom: 8px;">Drag and drop file here</h3>
            <p style="color: #6b7280; margin-bottom: 16px;">or</p>
        </div>
    """, unsafe_allow_html=True)


def format_time_ago(dt):
    """Format datetime to 'time ago' string"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days == 0:
        if diff.seconds < 3600:
            mins = diff.seconds // 60
            return f"{mins}m ago" if mins > 0 else "Just now"
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks}w ago"
    else:
        return dt.strftime("%b %d")