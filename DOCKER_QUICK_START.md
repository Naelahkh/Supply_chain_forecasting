# 🐳 Docker Quick Start Guide

Quick guide to get your Supply Chain Forecasting Agent running with Docker in minutes!

---

## 📋 Prerequisites

1. **Docker Desktop** installed
   - Windows/Mac: Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Linux: Follow [Docker installation guide](https://docs.docker.com/engine/install/)

2. **Verify Docker Installation**:
   ```bash
   docker --version
   docker-compose --version
   ```

---

## ⚡ Quick Start (3 Steps)

### Step 1: Create Environment File

Create a `.env` file in the project root:

**On Linux/Mac:**
```bash
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key_here
EOF
```

**On Windows (PowerShell):**
```powershell
echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
```

**On Windows (CMD):**
```cmd
echo GOOGLE_API_KEY=your_google_api_key_here > .env
```

### Step 2: Build and Start

**Using Scripts (Recommended):**

**Linux/Mac:**
```bash
# Make scripts executable
chmod +x docker-*.sh

# Build the image
./docker-build.sh

# Start the services
./docker-start.sh
```

**Windows:**
```cmd
# Build the image
docker-build.bat

# Start the services
docker-start.bat
```

**Using Docker Compose Directly:**
```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Step 3: Access Your Application

Once started, access:
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📝 Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Check Service Status
```bash
docker-compose ps
```

### Execute Commands in Container
```bash
# Backend container
docker-compose exec backend bash

# Frontend container
docker-compose exec frontend bash
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

**Error**: `Bind for 0.0.0.0:8501 failed: port is already allocated`

**Solution**:
1. Check what's using the port:
   ```bash
   # Linux/Mac
   lsof -i :8501
   # Windows
   netstat -ano | findstr :8501
   ```

2. Stop the service using the port or change ports in `docker-compose.yml`

### Issue: .env File Not Found

**Error**: `Environment variable GOOGLE_API_KEY not set`

**Solution**: Create a `.env` file with your API key (see Step 1)

### Issue: Container Won't Start

**Solution**:
1. Check logs: `docker-compose logs`
2. Check container status: `docker-compose ps`
3. Rebuild: `docker-compose build --no-cache`

### Issue: Models Not Loading

**Solution**:
1. Verify models directory exists: `ls models/`
2. Check volume mounts: `docker-compose config`
3. Check container logs: `docker-compose logs backend`

### Issue: Out of Memory

**Solution**: Adjust resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G  # Reduce if needed
```

---

## 🏗️ Project Structure

```
.
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose configuration
├── .dockerignore             # Files to exclude from Docker build
├── .env                      # Environment variables (create this)
├── requirements.txt          # Python dependencies
├── models/                   # ML model files (persisted)
├── knowledge_base/           # RAG knowledge base (persisted)
├── data/                     # User data (persisted)
└── logs/                     # Application logs (persisted)
```

---

## 📊 Resource Usage

The Docker setup is optimized for free cloud tiers:

- **Backend**: Max 2GB RAM, 1 CPU core
- **Frontend**: Max 2GB RAM, 1 CPU core
- **Total**: ~4GB RAM, 2 CPU cores maximum

You can adjust these in `docker-compose.yml` if needed.

---

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Use Docker secrets in production** - Don't rely on `.env` files
3. **Keep Docker images updated** - Regularly rebuild with latest base images
4. **Monitor logs** - Check for unauthorized access attempts

---

## 🚀 Next Steps

Once Docker is working locally:
1. ✅ Test all features
2. ✅ Verify health checks
3. ✅ Check logs for errors
4. 📅 **Tomorrow**: Deploy to Azure or Google Cloud (Free Tier)

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- Full deployment guide: `DOCKER_DEPLOYMENT_GUIDE.md`

---

**Need Help?** Check `DOCKER_DEPLOYMENT_GUIDE.md` for detailed instructions.

