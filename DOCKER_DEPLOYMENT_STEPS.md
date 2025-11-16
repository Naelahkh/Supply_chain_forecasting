# 🐳 Docker Deployment Steps - Complete Guide

Step-by-step guide to deploy your Supply Chain Forecasting Agent with Docker.

---

## ✅ Prerequisites Check

Docker and Docker Compose are installed:
- ✅ Docker version 28.4.0
- ✅ Docker Compose version v2.39.4

---

## 📋 Step-by-Step Deployment

### **Step 1: Create Environment File**

You need to create a `.env` file with your API keys.

**Option A: Copy from example and edit**
```powershell
# Copy the example file
Copy-Item env.example .env

# Then edit .env file and replace with your actual keys:
# - GOOGLE_API_KEY=your_actual_google_api_key
# - HUGGINGFACEHUB_API_TOKEN=your_actual_huggingface_token (optional)
```

**Option B: Create manually**
```powershell
# Create .env file with your keys
@"
GOOGLE_API_KEY=your_actual_google_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
"@ | Out-File -FilePath .env -Encoding utf8
```

**⚠️ Important**: Replace the placeholder values with your actual API keys!

---

### **Step 2: Verify Required Files**

Make sure these directories exist:
```powershell
# Check if required directories exist
Test-Path models
Test-Path knowledge_base
Test-Path data
Test-Path logs
```

If any are missing, create them:
```powershell
New-Item -ItemType Directory -Force -Path models, knowledge_base, data, logs
```

---

### **Step 3: Build Docker Images**

Build the Docker images (this downloads dependencies and creates the containers):

**Option A: Using helper script**
```powershell
.\docker-build.bat
```

**Option B: Using Docker Compose directly**
```powershell
docker-compose build
```

**Expected output**: Images will be built. This may take 5-10 minutes the first time.

---

### **Step 4: Start the Services**

Start the Docker containers:

**Option A: Using helper script**
```powershell
.\docker-start.bat
```

**Option B: Using Docker Compose directly**
```powershell
docker-compose up -d
```

**What happens**:
- Backend container starts (FastAPI on port 8000)
- Frontend container starts (Streamlit on port 8501)
- Services run in background (`-d` flag)

---

### **Step 5: Check Service Status**

Verify containers are running:

```powershell
docker-compose ps
```

**Expected output**:
```
NAME                STATUS          PORTS
forecast-backend    Up (healthy)    0.0.0.0:8000->8000/tcp
forecast-frontend   Up              0.0.0.0:8501->8501/tcp
```

---

### **Step 6: View Logs (Optional)**

Check if services started correctly:

```powershell
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Press Ctrl+C to exit log view
```

**Look for**:
- ✅ "Application startup complete" (backend)
- ✅ "You can now view your Streamlit app" (frontend)
- ❌ Any ERROR messages

---

### **Step 7: Test Health Check**

Verify the backend is healthy:

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Or open in browser
# http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "models_loaded": 5,
  "timestamp": "2025-01-15T...",
  "service": "forecast-api"
}
```

---

### **Step 8: Access Your Application**

Open in your browser:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8501 | Streamlit web interface |
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Service health status |

---

## 🧪 Testing Your Setup

Run the test script to verify everything works:

```powershell
.\docker-test.bat
```

This will check:
- ✅ Docker installation
- ✅ Environment file
- ✅ Models directory
- ✅ Knowledge base directory
- ✅ Container status
- ✅ Health checks

---

## 📝 Useful Commands

### Start Services
```powershell
docker-compose up -d
```

### Stop Services
```powershell
docker-compose down
```

### Restart Services
```powershell
docker-compose restart
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild After Code Changes
```powershell
docker-compose up -d --build
```

### Check Status
```powershell
docker-compose ps
```

### Stop and Remove Everything
```powershell
# Stop containers (keeps data)
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

**Error**: `Bind for 0.0.0.0:8501 failed: port is already allocated`

**Solution**:
```powershell
# Check what's using the port
netstat -ano | findstr :8501
netstat -ano | findstr :8000

# Stop the process using the port or change ports in docker-compose.yml
```

### Issue: .env File Not Found

**Error**: `Environment variable GOOGLE_API_KEY not set`

**Solution**:
```powershell
# Create .env file (see Step 1)
Copy-Item env.example .env
# Edit .env and add your API keys
```

### Issue: Container Won't Start

**Solution**:
```powershell
# Check logs
docker-compose logs

# Check configuration
docker-compose config

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Out of Memory

**Solution**: Edit `docker-compose.yml` and reduce memory limits:
```yaml
deploy:
  resources:
    limits:
      memory: 1G  # Reduce from 2G if needed
```

### Issue: Models Not Loading

**Solution**:
```powershell
# Verify models directory exists and has files
dir models

# Check volume mounts
docker-compose config

# Check container logs
docker-compose logs backend
```

---

## ✅ Deployment Checklist

Before considering deployment complete:

- [ ] `.env` file created with API keys
- [ ] Docker images built successfully
- [ ] Containers started and running
- [ ] Health check passes (`/health` endpoint)
- [ ] Frontend accessible at http://localhost:8501
- [ ] Backend accessible at http://localhost:8000
- [ ] No errors in logs
- [ ] Test script passes

---

## 🚀 Quick Commands Reference

```powershell
# Full deployment (build + start)
docker-compose up -d --build

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Test setup
.\docker-test.bat
```

---

## 🌐 Next: Cloud Deployment

Once Docker is working locally:
1. ✅ Test all features
2. ✅ Verify health checks
3. ✅ Check logs for errors
4. 📅 **Tomorrow**: Deploy to Azure or Google Cloud (Free Tier)

---

**Ready to start?** Begin with **Step 1** above! 🚀

