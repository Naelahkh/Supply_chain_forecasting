"""
Utility functions for Supply Chain AI Chatbot
"""
import streamlit as st
import json
import hashlib
from datetime import datetime
from pathlib import Path

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
CHATS_FILE = DATA_DIR / "chats.json"


def load_css(css_file=None):
    """Load CSS file"""
    import os
    import sys
    
    # Get the current working directory
    cwd = os.getcwd()
    
    # List of possible CSS file locations
    possible_paths = [
        os.path.join(cwd, 'styles', 'style.css'),
        os.path.join(cwd, '..', 'styles', 'style.css'),
        'styles/style.css',
        '../styles/style.css',
    ]
    
    # If specific file provided, try it first
    if css_file:
        possible_paths.insert(0, str(css_file))
    
    # Try each path until one works
    for path in possible_paths:
        try:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                return
        except Exception as e:
            continue
    
    # If no CSS file found, use inline basic styles
    st.markdown("""
        <style>
        .stButton > button {
            background: linear-gradient(135deg, #0073e6 0%, #005bb3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #005bb3 0%, #004280 100%);
            transform: translateY(-2px);
        }
        </style>
    """, unsafe_allow_html=True)


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def register_user(name, email, password):
    """Register a new user"""
    users = load_users()
    
    if email in users:
        return False, "Email already exists"
    
    users[email] = {
        'name': name,
        'password': hash_password(password),
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    return True, "Registration successful"


def login_user(email, password):
    """Login user"""
    users = load_users()
    
    if email not in users:
        return False, "Email not found"
    
    if users[email]['password'] != hash_password(password):
        return False, "Incorrect password"
    
    return True, users[email]


def load_chats(user_email):
    """Load chats for a specific user"""
    if CHATS_FILE.exists():
        with open(CHATS_FILE, 'r') as f:
            all_chats = json.load(f)
            return all_chats.get(user_email, [])
    return []


def save_chats(user_email, chats):
    """Save chats for a specific user"""
    if CHATS_FILE.exists():
        with open(CHATS_FILE, 'r') as f:
            all_chats = json.load(f)
    else:
        all_chats = {}
    
    all_chats[user_email] = chats
    
    with open(CHATS_FILE, 'w') as f:
        json.dump(all_chats, f, indent=2)


def create_new_chat(title="New Conversation"):
    """Create a new chat"""
    return {
        'id': datetime.now().timestamp(),
        'title': title,
        'messages': [],
        'created_at': datetime.now().isoformat(),
        'has_data': False,
        'uploaded_file': None
    }


def add_message(chat, content, type='user', chart_data=None):
    """Add a message to chat"""
    message = {
        'id': datetime.now().timestamp(),
        'type': type,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'chart_data': chart_data
    }
    chat['messages'].append(message)
    return chat


def format_datetime(dt_string):
    """Format datetime string"""
    dt = datetime.fromisoformat(dt_string)
    now = datetime.now()
    diff = now - dt
    
    if diff.days == 0:
        return "Today"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    elif diff.days < 30:
        return f"{diff.days // 7} weeks ago"
    else:
        return dt.strftime("%b %d, %Y")


def generate_bot_response(user_message, has_data=False):
    """Generate bot response based on user message"""
    message_lower = user_message.lower()
    
    if not has_data:
        return {
            'content': "Please upload your data file first to start analysis. Click the 'Upload File' button in the sidebar.",
            'chart_data': None
        }
    
    # Check for analysis request
    if 'analyze' in message_lower or 'analysis' in message_lower:
        chart_data = {
            'type': 'line',
            'labels': ['January', 'February', 'March', 'April', 'May', 'June'],
            'values': [65000, 78000, 82000, 91000, 105000, 125000],
            'title': 'Sales Trend Analysis'
        }
        return {
            'content': """Analysis completed! ✨

Here's your data summary:

📈 **Total Sales**: $1,234,567
📊 **Number of Orders**: 4,532
🎯 **Average Order Value**: $272
📉 **Growth Rate**: +15.3%

The chart below shows the sales trend over the last 6 months.""",
            'chart_data': chart_data
        }
    
    # Check for forecast request
    if 'forecast' in message_lower or 'predict' in message_lower:
        return {
            'content': """Forecasting future values... 🔮

**Predictions for upcoming months:**

📅 July 2024: $135,000
📅 August 2024: $142,000
📅 September 2024: $156,000

**Model Accuracy**: 96.8%
**Confidence Level**: High

Would you like to see more details or analyze the influencing factors?""",
            'chart_data': None
        }
    
    # Check for statistics request
    if 'statistic' in message_lower or 'stats' in message_lower:
        return {
            'content': """Here are your key statistics:

📊 **Summary Statistics:**
• Mean Sales: $98,500
• Median Sales: $91,000
• Standard Deviation: $18,200
• Min Value: $65,000
• Max Value: $125,000

📈 **Growth Metrics:**
• Month-over-Month Growth: 11.2%
• Quarter-over-Quarter Growth: 32.5%
• Year-over-Year Growth: 45.8%

What else would you like to know?""",
            'chart_data': None
        }
    
    # Default response
    return {
        'content': """I understand your question! 🤖

I can help you with:
• Analyzing your uploaded data
• Forecasting future sales
• Displaying detailed statistics
• Creating interactive charts

What would you like me to do?""",
        'chart_data': None
    }


def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is valid"
