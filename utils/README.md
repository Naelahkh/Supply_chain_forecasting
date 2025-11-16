# Supply Chain AI Chatbot 🤖

**Intelligent Supply Chain Data Analytics Platform powered by AI**

A complete web-based interactive chatbot specialized in Supply Chain Analytics. Built with Streamlit and Python, featuring advanced data analysis, forecasting, and conversational AI capabilities.

## 🌟 Features

- **Landing Page** - Professional welcome page explaining system features
- **Authentication System** - Secure login and registration
- **Interactive Chat Interface** - Conversational AI for data analysis
- **File Upload** - Support for CSV and Excel files
- **Smart Analysis** - Comprehensive data analysis with visualizations
- **Future Forecasting** - Predict sales and revenue trends
- **Chat History** - Save and manage conversation history
- **Real-time Charts** - Interactive data visualizations with Plotly

## 🛠 Tech Stack

### Core
- **Streamlit 1.29.0** - Web framework
- **Python 3.8+** - Programming language
- **Pandas 2.1.4** - Data manipulation
- **Plotly 5.18.0** - Interactive charts

### Additional
- **JSON** - Data storage
- **Hashlib** - Password hashing
- **Custom CSS/HTML** - Styling

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Extract the ZIP file**

```bash
unzip supply-chain-streamlit.zip
cd supply-chain-streamlit
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the application**

```bash
streamlit run app.py
```

4. **Open in browser**

The app will automatically open in your default browser at:
```
http://localhost:8501
```

## 📁 Project Structure

```
supply-chain-streamlit/
├── app.py                      # Main application (Landing Page)
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── pages/
│   ├── 1_🔐_Auth.py           # Authentication page
│   └── 2_💬_Chat.py           # Chat interface
├── components/
│   └── ui_components.py       # Reusable UI components
├── utils/
│   └── helpers.py             # Utility functions
├── styles/
│   └── style.css              # Custom CSS styles
├── data/                       # Data storage (auto-created)
│   ├── users.json             # User accounts
│   └── chats.json             # Chat history
└── README.md                   # This file
```

## 🎨 Design

### Color Scheme
- **Primary Blue**: `#0073e6`
- **Light Blue**: `#e6f2ff`
- **Dark Blue**: `#004280`
- **White**: `#ffffff`
- **Gray Shades**: `#f9fafb` to `#111827`

### Features
- Clean and modern interface
- Responsive design (works on all devices)
- Smooth animations and transitions
- Intuitive user experience

## 📱 Pages Overview

### 1. Landing Page (`app.py`)
- Welcome screen with feature highlights
- How It Works section (3 steps)
- Key Features showcase
- Call-to-action buttons
- Professional footer

### 2. Authentication Page (`pages/1_🔐_Auth.py`)
- Login form with validation
- Sign-up form with password confirmation
- Email format validation
- Password strength checking
- Secure password hashing (SHA256)

### 3. Chat Interface (`pages/2_💬_Chat.py`)
- Sidebar with chat history
- File upload functionality
- Real-time message display
- Quick action buttons
- Interactive charts with Plotly
- Chat title editing
- Delete conversations
- User profile section

## 🔐 Security Features

- Password hashing (SHA256)
- Session state management
- Form validation
- XSS protection (Streamlit built-in)
- Secure file handling

## 💾 Data Management

### Storage
- JSON files for data persistence
- Separate files for users and chats
- Automatic data directory creation

### User Data
```json
{
  "email@example.com": {
    "name": "John Doe",
    "password": "hashed_password",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### Chat Data
```json
{
  "email@example.com": [
    {
      "id": 1234567890,
      "title": "Conversation Title",
      "messages": [...],
      "created_at": "2024-01-01T00:00:00",
      "has_data": true,
      "uploaded_file": "data.csv"
    }
  ]
}
```

## 🎯 User Flow

```
1. Landing Page (/)
   ↓
2. Authentication (Login/Sign Up)
   ↓
3. Chat Interface
   ↓
4. Upload Data File
   ↓
5. Chat with AI
   ↓
6. Get Analysis/Forecast
```

## 📊 Features in Detail

### Data Analysis
- Upload CSV/Excel files
- Automatic data parsing
- Statistical analysis
- Interactive visualizations
- Key metrics display

### Forecasting
- Time series prediction
- Sales forecasting
- Revenue prediction
- Confidence levels
- Model accuracy metrics

### Chat Features
- Natural language processing
- Context-aware responses
- Quick action buttons
- Message history
- Timestamp display
- User/Bot differentiation

## 🎨 Customization

### Change Colors
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#0073e6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#111827"
```

### Modify Styles
Edit `styles/style.css` for custom CSS

### Add Features
- Components in `components/ui_components.py`
- Utilities in `utils/helpers.py`
- New pages in `pages/` directory

## 🔧 Configuration

### Streamlit Settings
Configure in `.streamlit/config.toml`:
- Theme colors
- Server settings
- Port configuration
- CORS settings

### Environment Variables
Create `.env` file (optional):
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

## 📈 Performance

### Optimizations
- Efficient data caching
- Lazy loading of components
- Optimized chart rendering
- Minimal re-runs

### Scalability
- JSON storage for MVP
- Can be upgraded to:
  - PostgreSQL/MySQL for users
  - MongoDB for chat history
  - Redis for caching

## 🐛 Troubleshooting

### Common Issues

**Issue**: Module not found
```bash
pip install -r requirements.txt
```

**Issue**: Port already in use
```bash
streamlit run app.py --server.port 8502
```

**Issue**: Permission denied (data folder)
```bash
chmod 755 data/
```

**Issue**: Streamlit not found
```bash
pip install streamlit --upgrade
```

## 🚀 Deployment

### Local
```bash
streamlit run app.py
```

### Cloud Options
1. **Streamlit Cloud** (Free)
   - Connect GitHub repo
   - Auto-deploy on push

2. **Heroku**
   - Add `Procfile`: `web: streamlit run app.py`
   - Add `setup.sh` for configuration

3. **AWS/GCP/Azure**
   - Use Docker container
   - Deploy on compute instance

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 🔄 Future Enhancements

### Planned Features
- [ ] Real backend API integration
- [ ] XGBoost model integration
- [ ] RAG system for recommendations
- [ ] Export results (PDF/Excel)
- [ ] Multi-language support
- [ ] Advanced charting options
- [ ] Real-time collaboration
- [ ] Mobile app version

### Integration Ready
- REST API endpoints
- Database connections
- ML model deployment
- Cloud storage
- Authentication providers (OAuth)

## 📚 Documentation

### For Users
- Simple and intuitive interface
- Tooltips and help text
- Error messages with solutions

### For Developers
- Well-commented code
- Modular structure
- Clear naming conventions
- Type hints (where applicable)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available for free use.

## 📞 Support

For issues or questions:
1. Check the README
2. Review code comments
3. Check Streamlit documentation
4. Open an issue on GitHub

## 🎓 Learning Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Charts](https://plotly.com/python/)
- [Pandas Guide](https://pandas.pydata.org/docs/)

## ⚡ Commands Cheat Sheet

```bash
# Run application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Check Streamlit version
streamlit version

# Clear cache
streamlit cache clear

# Run on specific port
streamlit run app.py --server.port 8502

# Run without browser
streamlit run app.py --server.headless true
```

## 🎉 Credits

Built with ❤️ for Supply Chain Analytics

**Technologies Used:**
- Streamlit
- Python
- Plotly
- Pandas
- HTML/CSS

---

**Ready to use! 🚀**

Start the app: `streamlit run app.py`
