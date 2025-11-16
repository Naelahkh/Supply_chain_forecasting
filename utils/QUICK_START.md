# 🚀 Quick Start Guide - Supply Chain AI Chatbot

## ⚡ Get Started in 3 Minutes!

### Step 1: Install Python 📥
Make sure you have Python 3.8 or higher installed:
```bash
python --version
```

Download from: https://www.python.org/downloads/

### Step 2: Extract & Navigate 📂
```bash
unzip supply-chain-streamlit.zip
cd supply-chain-streamlit
```

### Step 3: Install Dependencies 📦
```bash
pip install -r requirements.txt
```

⏳ Wait 1-2 minutes for installation...

### Step 4: Run the App 🎉
```bash
streamlit run app.py
```

### Step 5: Open Browser 🌐
The app will automatically open at:
```
http://localhost:8501
```

## ✨ That's it! You're ready to go!

---

## 📱 How to Use

### 1. Landing Page
- Click "Sign Up" to create an account
- Or "Login" if you already have one

### 2. Authentication
- **Sign Up**: Enter name, email, and password
- **Login**: Enter email and password

### 3. Chat Interface
- Click "➕ New Conversation" to start
- Upload a CSV or Excel file
- Choose quick actions or type your question
- Get instant AI-powered analysis!

---

## 🎯 Quick Actions

Once you upload a file, try these:

- **📊 Analyze Data** - Get comprehensive analysis
- **🔮 Forecast Future** - Predict future trends
- **📈 Show Statistics** - View key metrics

---

## 💡 Sample Questions

Ask the AI chatbot:
- "Analyze the uploaded data"
- "Forecast sales for next 3 months"
- "Show me the key statistics"
- "What are the trends in my data?"

---

## 🛠 Useful Commands

```bash
# Run app
streamlit run app.py

# Run on different port
streamlit run app.py --server.port 8502

# Clear cache
streamlit cache clear

# Check version
streamlit version
```

---

## ❓ Troubleshooting

### Problem: "pip: command not found"
**Solution**: Install Python first from python.org

### Problem: "streamlit: command not found"
**Solution**: 
```bash
pip install streamlit
```

### Problem: "Port 8501 already in use"
**Solution**:
```bash
streamlit run app.py --server.port 8502
```

### Problem: Missing modules
**Solution**:
```bash
pip install -r requirements.txt
```

---

## 📊 Project Structure

```
supply-chain-streamlit/
├── app.py              # Landing page (start here)
├── pages/
│   ├── 1_🔐_Auth.py   # Login/Signup
│   └── 2_💬_Chat.py   # Chat interface
├── data/               # Your data storage
└── requirements.txt    # Dependencies
```

---

## 🎨 Features at a Glance

✅ Professional landing page
✅ Secure authentication
✅ Interactive chat interface
✅ File upload (CSV/Excel)
✅ AI-powered analysis
✅ Beautiful charts
✅ Chat history
✅ Responsive design

---

## 🔐 Security

- Passwords are hashed (SHA256)
- Session-based authentication
- Secure file handling
- Data stored locally in JSON

---

## 💻 System Requirements

- **OS**: Windows, Mac, or Linux
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum
- **Disk**: 100MB free space

---

## 📈 Next Steps

1. ✅ Create an account
2. ✅ Upload sample data
3. ✅ Try different analyses
4. ✅ Explore chat features
5. ✅ Customize settings

---

## 🎓 Need Help?

- Check **README.md** for full documentation
- Review code comments
- Visit [Streamlit Docs](https://docs.streamlit.io)

---

## 🚀 Ready to Go!

Just run:
```bash
streamlit run app.py
```

**Enjoy your Supply Chain AI experience! 🎉**
