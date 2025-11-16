# 🐳 Docker Deployment Guide

Complete step-by-step guide to deploy your Supply Chain Forecasting Agent using Docker.

---

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)
- Google API Key
- Git (optional, for version control)

---

## 🚀 Quick Start (Local Testing)

### Step 1: Prepare Your Environment

1. **Create `.env` file** in the project root:
```bash
# Copy the example (if you have one)
cp .env.example .env

# Or create manually
touch .env
```

2. **Add your API key to `.env`**:
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
```

### Step 2: Build and Run

```bash
# Build the Docker images
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Step 3: Access Your Application

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 4: Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clears data)
docker-compose down -v
```

---

## 🔧 Detailed Setup

### 1. Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Test Docker
docker run hello-world
```

### 2. Project Structure

Your project should have:
```
Supply_Chain_Forecasting_Agent_3/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env
├── requirements.txt
├── web_app_v2.py
├── unified_forecaster_app.py
├── app_v8.py
├── rag_engine.py
├── models/
├── knowledge_base/
├── data/
└── ... (other files)
```

### 3. Environment Variables

Create `.env` file with:
```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional (defaults work fine)
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_SERVER_PORT=8501
```

**⚠️ Important:** Never commit `.env` file to Git!

---

## 🏗️ Building the Docker Image

### Option 1: Using Docker Compose (Recommended)

```bash
# Build images
docker-compose build

# Build without cache (if you have issues)
docker-compose build --no-cache

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Option 2: Using Docker Directly

```bash
# Build the image
docker build -t forecast-app:latest .

# Tag for registry (if pushing)
docker tag forecast-app:latest your-registry/forecast-app:latest
```

---

## 🚢 Running the Application

### Development Mode (with logs)

```bash
# Run in foreground (see logs)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Production Mode

```bash
# Run in detached mode
docker-compose up -d

# Check status
docker-compose ps

# Check health
docker-compose ps
# Should show "healthy" for backend
```

---

## 🔍 Useful Docker Commands

### View Running Containers
```bash
docker-compose ps
# or
docker ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Execute Commands in Container
```bash
# Access backend container shell
docker-compose exec backend bash

# Access frontend container shell
docker-compose exec frontend bash

# Run Python command
docker-compose exec backend python -c "import streamlit; print('OK')"
```

### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Stop and Remove
```bash
# Stop services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers and volumes (⚠️ deletes data)
docker-compose down -v

# Remove images too
docker-compose down --rmi all
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose build frontend
docker-compose up -d frontend
```

---

## 🌐 Deploying to Production

### Option 1: Deploy to VPS (DigitalOcean, Linode, etc.)

#### Step 1: Set Up Server

```bash
# SSH into your server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Step 2: Transfer Your Project

```bash
# On your local machine
# Option A: Using Git
git clone your-repo-url
cd Supply_Chain_Forecasting_Agent_3

# Option B: Using SCP
scp -r /path/to/project user@server:/home/user/

# On server
cd /home/user/Supply_Chain_Forecasting_Agent_3
```

#### Step 3: Create .env File on Server

```bash
# Create .env file
nano .env

# Add your API key
GOOGLE_API_KEY=your_key_here
```

#### Step 4: Deploy

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 5: Set Up Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/forecast-app
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (Streamlit)
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/forecast-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Option 2: Deploy to Cloud Platforms

#### AWS (ECS/Fargate)

1. Push image to ECR (Elastic Container Registry)
2. Create ECS task definition
3. Create ECS service
4. Set up Application Load Balancer

#### Google Cloud (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/forecast-app

# Deploy to Cloud Run
gcloud run deploy forecast-app \
  --image gcr.io/PROJECT-ID/forecast-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure (Container Instances)

```bash
# Build and push to ACR
az acr build --registry myregistry --image forecast-app:latest .

# Deploy
az container create \
  --resource-group myResourceGroup \
  --name forecast-app \
  --image myregistry.azurecr.io/forecast-app:latest \
  --dns-name-label forecast-app \
  --ports 8501 8000
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

```bash
# Use Docker secrets or environment files
# Never hardcode secrets in Dockerfile

# Use .env file (already in .gitignore)
# Or use Docker secrets in production
```

### 2. Network Security

```bash
# Only expose necessary ports
# Use internal Docker networks
# Set up firewall rules on host
```

### 3. Image Security

```bash
# Use specific version tags, not 'latest'
# Regularly update base images
# Scan images for vulnerabilities
docker scan forecast-app:latest
```

### 4. Resource Limits

Add to `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 📊 Monitoring & Maintenance

### Health Checks

The Dockerfile includes a health check. Monitor it:

```bash
# Check container health
docker ps
# Look for "healthy" status

# View health check logs
docker inspect forecast-backend | grep -A 10 Health
```

### Logs Management

```bash
# Configure log rotation in docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Backup Data

```bash
# Backup user data
docker-compose exec backend tar -czf /tmp/backup.tar.gz /app/data
docker cp forecast-backend:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz

# Restore data
docker cp ./backup-20250115.tar.gz forecast-backend:/tmp/
docker-compose exec backend tar -xzf /tmp/backup.tar.gz -C /app/
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Or for zero-downtime (advanced)
docker-compose up -d --build --no-deps frontend
```

---

## 🐛 Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs

# Check container status
docker-compose ps

# Check if ports are in use
sudo lsof -i :8000
sudo lsof -i :8501
```

### Issue: Models not loading

```bash
# Verify models directory is mounted
docker-compose exec backend ls -la /app/models

# Check file permissions
docker-compose exec backend ls -l /app/models/
```

### Issue: API key errors

```bash
# Verify environment variable
docker-compose exec backend env | grep GOOGLE_API_KEY

# Check .env file
cat .env
```

### Issue: Out of memory

```bash
# Check container resource usage
docker stats

# Increase memory limits in docker-compose.yml
# Or upgrade your server
```

### Issue: Can't connect to backend

```bash
# Check if backend is healthy
docker-compose ps

# Test backend directly
curl http://localhost:8000/health

# Check network
docker network inspect forecast-network
```

---

## 📝 Production Checklist

Before going live:

- [ ] `.env` file configured with production API key
- [ ] All models present in `models/` directory
- [ ] Knowledge base files complete
- [ ] Health checks working
- [ ] Logs configured and monitored
- [ ] Backups set up
- [ ] SSL certificate installed
- [ ] Firewall rules configured
- [ ] Resource limits set
- [ ] Monitoring tools configured
- [ ] Documentation updated

---

## 🎯 Quick Reference

### Most Common Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Restart a service
docker-compose restart frontend

# Check status
docker-compose ps
```

---

## 📞 Need Help?

- Check logs: `docker-compose logs -f`
- Check container status: `docker-compose ps`
- Access container: `docker-compose exec backend bash`
- View Docker documentation: https://docs.docker.com/

---

**Last Updated**: 2025-01-15
**Version**: 1.0

