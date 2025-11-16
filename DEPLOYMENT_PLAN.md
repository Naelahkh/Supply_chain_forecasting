# 🚀 Deployment Plan for Supply Chain Forecasting Agent

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Dependencies & Requirements](#dependencies--requirements)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Deployment Options](#deployment-options)
7. [Security Considerations](#security-considerations)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## ✅ Pre-Deployment Checklist

### Code Readiness
- [ ] All features tested and working
- [ ] No critical bugs or errors
- [ ] Code is clean and documented
- [ ] All environment variables identified
- [ ] Dependencies documented in `requirements.txt`
- [ ] Models are trained and saved in `models/` directory
- [ ] Knowledge base files are complete

### Files to Verify
- [ ] `web_app_v2.py` - Main Streamlit app
- [ ] `unified_forecaster_app.py` - FastAPI backend
- [ ] `rag_engine.py` - RAG chain
- [ ] `app_v8.py` - Chat interface
- [ ] All model files in `models/` directory
- [ ] Knowledge base files in `knowledge_base/` directory
- [ ] `requirements.txt` - All dependencies listed

---

## 🔧 Environment Setup

### 1. Update Requirements File

**Current `requirements.txt` is incomplete!** Update it with all dependencies:

```txt
# Web Framework
streamlit==1.29.0
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Data Processing
pandas==2.1.4
numpy==1.24.3

# Machine Learning
scikit-learn==1.3.2
lightgbm==4.1.0
xgboost==2.0.3
prophet==1.1.5
tensorflow==2.15.0
statsmodels==0.14.0

# LLM & RAG
langchain==0.1.0
langchain-google-genai==0.0.6
langchain-community==0.0.20
langchain-huggingface==0.0.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4

# Visualization
plotly==5.18.0
matplotlib==3.8.2

# Utilities
python-dateutil==2.8.2
Pillow==10.1.0
python-dotenv==1.0.0
requests==2.31.0
openpyxl==3.1.2
joblib==1.3.2
pydantic==2.5.0
```

### 2. Create `.env` File Template

Create a `.env.example` file (DO NOT commit actual `.env`):

```env
# Google AI API Key (Required)
GOOGLE_API_KEY=your_google_api_key_here

# FastAPI Settings (Optional)
API_HOST=127.0.0.1
API_PORT=8000

# Streamlit Settings (Optional)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Environment
ENVIRONMENT=production
```

### 3. Create `.gitignore` (if not exists)

Ensure sensitive files are ignored:
```
.env
.env.local
*.pkl
*.h5
*.joblib
__pycache__/
*.pyc
data/users.json
data/chats.json
models/*.pkl
models/*.h5
models/*.joblib
.streamlit/secrets.toml
```

---

## 📦 Dependencies & Requirements

### System Requirements
- **Python**: 3.9 or higher (3.10+ recommended)
- **RAM**: Minimum 4GB (8GB+ recommended for ML models)
- **Disk Space**: At least 2GB for models and dependencies
- **OS**: Linux, Windows, or macOS

### Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Verify Installation

```bash
# Test imports
python -c "import streamlit; import fastapi; import tensorflow; print('All imports successful')"

# Check API key
python -c "from rag_engine import check_api_key; check_api_key()"
```

---

## ⚙️ Configuration

### 1. Environment Variables

**Required:**
- `GOOGLE_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional:**
- `API_HOST` - FastAPI host (default: 127.0.0.1)
- `API_PORT` - FastAPI port (default: 8000)
- `STREAMLIT_SERVER_PORT` - Streamlit port (default: 8501)

### 2. Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#0073e6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#111827"
```

### 3. FastAPI Configuration

The FastAPI app (`unified_forecaster_app.py`) should be configured to:
- Run on port 8000 (or configured port)
- Allow CORS if needed
- Handle timeouts for long-running forecasts

---

## 🧪 Testing

### 1. Local Testing

**Step 1: Start FastAPI Backend**
```bash
# Terminal 1
cd /path/to/project
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn unified_forecaster_app:app --reload --host 127.0.0.1 --port 8000
```

**Step 2: Start Streamlit Frontend**
```bash
# Terminal 2
cd /path/to/project
source venv/bin/activate
streamlit run web_app_v2.py
```

**Step 3: Test Endpoints**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/docs (FastAPI docs)
- Health check: http://localhost:8000/health (if implemented)

### 2. Test Checklist

- [ ] User can sign up/login
- [ ] User can upload CSV/Excel file
- [ ] Data validation works
- [ ] RAG agent responds to queries
- [ ] Forecast generation works
- [ ] All models load correctly
- [ ] Charts display properly
- [ ] Interpretation includes business feedback
- [ ] Data export works

### 3. Load Testing

Test with:
- Multiple concurrent users
- Large data files (1000+ rows)
- Long forecast horizons (12+ months)
- Multiple model types

---

## 🌐 Deployment Options

### Option 1: Cloud Platform (Recommended)

#### A. Streamlit Cloud (Easiest)
**Pros:** Free tier, easy setup, automatic HTTPS
**Cons:** Limited to Streamlit apps only

**Steps:**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Set environment variables in dashboard
5. Deploy!

**Note:** FastAPI backend needs separate hosting

#### B. Heroku
**Pros:** Easy deployment, free tier available
**Cons:** Free tier discontinued, paid plans required

**Steps:**
1. Create `Procfile`:
```
web: uvicorn unified_forecaster_app:app --host 0.0.0.0 --port $PORT
streamlit: streamlit run web_app_v2.py --server.port=$PORT --server.address=0.0.0.0
```

2. Create `runtime.txt`:
```
python-3.10.12
```

3. Deploy:
```bash
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your_key
git push heroku main
```

#### C. AWS (EC2 + Elastic Beanstalk)
**Pros:** Scalable, professional
**Cons:** More complex setup, costs money

**Steps:**
1. Launch EC2 instance (t3.medium or larger)
2. Install dependencies
3. Use Elastic Beanstalk or Docker
4. Configure security groups
5. Set up domain and SSL

#### D. Google Cloud Platform (GCP)
**Pros:** Good ML integration, scalable
**Cons:** Complex setup

**Steps:**
1. Create Compute Engine instance
2. Install dependencies
3. Use Cloud Run for containers
4. Set up Cloud Load Balancer

#### E. DigitalOcean / Linode
**Pros:** Simple, affordable VPS
**Cons:** Manual setup required

**Steps:**
1. Create Droplet (4GB RAM minimum)
2. SSH into server
3. Install Python, dependencies
4. Set up systemd services
5. Configure Nginx reverse proxy

### Option 2: Docker Deployment (Recommended for Production)

**Create `Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Start both services
CMD ["sh", "-c", "uvicorn unified_forecaster_app:app --host 0.0.0.0 --port 8000 & streamlit run web_app_v2.py --server.port=8501 --server.address=0.0.0.0"]
```

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./models:/app/models
      - ./knowledge_base:/app/knowledge_base
      - ./data:/app/data

  frontend:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - backend
```

**Deploy:**
```bash
docker-compose up -d
```

### Option 3: VPS Manual Deployment

**Steps:**
1. **Server Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3.10 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y
```

2. **Application Setup:**
```bash
# Clone repository
git clone <your-repo-url>
cd Supply_Chain_Forecasting_Agent_3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your_key_here"
```

3. **Create Systemd Services:**

**`/etc/systemd/system/forecast-api.service`:**
```ini
[Unit]
Description=Forecast API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="GOOGLE_API_KEY=your_key"
ExecStart=/path/to/project/venv/bin/uvicorn unified_forecaster_app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/forecast-web.service`:**
```ini
[Unit]
Description=Forecast Web Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="GOOGLE_API_KEY=your_key"
ExecStart=/path/to/project/venv/bin/streamlit run web_app_v2.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Start Services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable forecast-api forecast-web
sudo systemctl start forecast-api forecast-web
sudo systemctl status forecast-api forecast-web
```

5. **Configure Nginx:**

**`/etc/nginx/sites-available/forecast-app`:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/forecast-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. **SSL Certificate (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 🔒 Security Considerations

### 1. Environment Variables
- ✅ Never commit `.env` file
- ✅ Use secure secret management (AWS Secrets Manager, HashiCorp Vault)
- ✅ Rotate API keys regularly
- ✅ Use different keys for dev/staging/production

### 2. API Security
- ✅ Implement rate limiting
- ✅ Add authentication to FastAPI endpoints
- ✅ Validate all user inputs
- ✅ Sanitize file uploads
- ✅ Use HTTPS in production

### 3. Data Security
- ✅ Encrypt sensitive data at rest
- ✅ Use secure file storage
- ✅ Implement data retention policies
- ✅ Regular backups
- ✅ Access controls

### 4. Application Security
- ✅ Keep dependencies updated
- ✅ Regular security audits
- ✅ Input validation
- ✅ SQL injection prevention (if using database)
- ✅ XSS protection

---

## 📊 Monitoring & Maintenance

### 1. Logging

**Add logging to key files:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Health Checks

**Add to `unified_forecaster_app.py`:**
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": len(LOADED_MODELS),
        "timestamp": datetime.now().isoformat()
    }
```

### 3. Monitoring Tools

- **Application Monitoring**: Sentry, New Relic, Datadog
- **Server Monitoring**: Prometheus, Grafana
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Error Tracking**: Sentry, Rollbar

### 4. Backup Strategy

**Automated Backups:**
- User data (`data/users.json`, `data/chats.json`)
- Model files (if retrained)
- Configuration files
- Knowledge base files

**Schedule:**
- Daily backups for user data
- Weekly backups for models
- Version control for code

### 5. Maintenance Tasks

**Weekly:**
- Check logs for errors
- Monitor API usage
- Review user feedback

**Monthly:**
- Update dependencies
- Review and optimize performance
- Security audit
- Backup verification

**Quarterly:**
- Model retraining (if needed)
- Performance optimization
- Feature updates
- Documentation updates

---

## 🚦 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Requirements.txt complete
- [ ] Environment variables documented
- [ ] Security review completed
- [ ] Backup strategy in place

### Deployment Day
- [ ] Deploy to staging first
- [ ] Test all features in staging
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor logs for errors
- [ ] Test critical user flows

### Post-Deployment
- [ ] Monitor for 24-48 hours
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan next iteration

---

## 📝 Quick Start Commands

### Local Development
```bash
# Terminal 1 - Backend
uvicorn unified_forecaster_app:app --reload

# Terminal 2 - Frontend
streamlit run web_app_v2.py
```

### Production Deployment
```bash
# Using systemd
sudo systemctl start forecast-api forecast-web

# Using Docker
docker-compose up -d

# Using PM2 (Node.js process manager for Python)
pm2 start uvicorn --name api -- unified_forecaster_app:app
pm2 start streamlit --name web -- run web_app_v2.py
```

---

## 🆘 Troubleshooting

### Common Issues

**Issue: Models not loading**
- Check model files exist in `models/` directory
- Verify file permissions
- Check model compatibility with TensorFlow version

**Issue: API key errors**
- Verify `GOOGLE_API_KEY` is set
- Check API key is valid
- Review API quota/limits

**Issue: Port conflicts**
- Change ports in configuration
- Check what's using the ports: `lsof -i :8000` or `netstat -an | grep 8000`

**Issue: Memory errors**
- Increase server RAM
- Optimize model loading
- Use model quantization

---

## 📞 Support & Resources

- **Documentation**: Check `utils/README.md`
- **Test Queries**: See `utils/TEST_QUERIES_BY_MODEL.md`
- **Model Guide**: See `utils/MODEL_SELECTION_GUIDE.md`

---

**Last Updated**: 2025-01-15
**Version**: 1.0

