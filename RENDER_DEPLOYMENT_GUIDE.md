# 🚀 Render Deployment Guide - Quick & Easy

Render is perfect for your needs: **free tier, easy setup, GitHub integration, and Docker support!**

## ✅ Why Render?

- ✅ **Free tier** for both backend and frontend
- ✅ **GitHub integration** - Auto-deploy on every push
- ✅ **Docker support** - Use your existing Dockerfile
- ✅ **Simple setup** - Web-based, no CLI needed
- ✅ **HTTPS by default** - Secure out of the box
- ✅ **Easy environment variables** - Set in web dashboard

---

## 📋 Prerequisites

1. **GitHub repository** ✅ (You already have this: `Naelahkh/Supply_chain_forecasting`)
2. **Render account** - Sign up at [render.com](https://render.com) (free)
3. **Docker images** - Your Dockerfile is ready ✅

---

## 🎯 Step-by-Step Deployment

### Step 1: Sign Up for Render

1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with GitHub (easiest option)
4. Authorize Render to access your GitHub repositories

### Step 2: Deploy Backend (FastAPI)

1. **In Render Dashboard:**
   - Click **"New +"** button
   - Select **"Web Service"**

2. **Connect Repository:**
   - Select your GitHub account
   - Choose repository: `Supply_chain_forecasting`
   - Click **"Connect"**

3. **Configure Backend Service:**
   
   **Basic Settings:**
   - **Name:** `forecast-backend`
   - **Region:** Choose closest to you (e.g., `Oregon (US West)`)
   - **Branch:** `main`
   - **Root Directory:** (leave empty)

   **Build & Deploy:**
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `Dockerfile.backend` (created for you ✅)
   - **Docker Context:** `.` (root directory)

   **Instance Type:**
   - **Free:** Select Free tier (1 CPU, 512MB RAM)
   - Or **Starter:** $7/month (better performance)

   **Advanced Settings:**
   - **Start Command:** (leave empty - Dockerfile handles this)
   - **Health Check Path:** `/health` (optional, but recommended)

4. **Environment Variables:**
   Click **"Add Environment Variable"** and add:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
   API_HOST=0.0.0.0
   PYTHONUNBUFFERED=1
   LOG_LEVEL=INFO
   ```

   **Note:** Render automatically sets `PORT=10000` environment variable. Our Dockerfile handles this automatically! ✅

5. **Click "Create Web Service"**

6. **Wait for deployment** (~5-10 minutes for first build)

7. **Copy the URL** - It will look like: `https://forecast-backend.onrender.com`

### Step 3: Deploy Frontend (Streamlit)

1. **In Render Dashboard:**
   - Click **"New +"** button
   - Select **"Web Service"**

2. **Connect Repository:**
   - Select your GitHub account
   - Choose repository: `Supply_chain_forecasting`
   - Click **"Connect"**

3. **Configure Frontend Service:**
   
   **Basic Settings:**
   - **Name:** `forecast-frontend`
   - **Region:** Same as backend
   - **Branch:** `main`
   - **Root Directory:** (leave empty)

   **Build & Deploy:**
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `Dockerfile.frontend` (created for you ✅)
   - **Docker Context:** `.` (root directory)

   **Instance Type:**
   - **Free:** Select Free tier
   - Or **Starter:** $7/month (better performance)

   **Advanced Settings:**
   - **Start Command:** (leave empty)
   - **Health Check Path:** `/` (or leave empty)

4. **Environment Variables:**
   Add all of these:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
   BACKEND_URL=https://forecast-backend.onrender.com
   STREAMLIT_SERVER_ADDRESS=0.0.0.0
   STREAMLIT_SERVER_HEADLESS=true
   STREAMLIT_SERVER_ENABLE_CORS=false
   STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
   PYTHONUNBUFFERED=1
   ```

   **Important:** 
   - Use the backend URL from Step 2 (e.g., `https://forecast-backend.onrender.com`)
   - Render automatically sets `PORT=10000` - no need to set `STREAMLIT_SERVER_PORT` ✅

5. **Click "Create Web Service"**

6. **Wait for deployment** (~5-10 minutes)

7. **Your app is live!** Frontend URL: `https://forecast-frontend.onrender.com`

---

## 🔧 Update Dockerfile for Render

Render uses port `10000` by default. Let's create Render-specific Dockerfiles:

### Option 1: Update unified_forecaster_app.py to use port from env

The backend already uses `API_PORT` from environment, but we need to make sure it defaults to 10000 for Render.

### Option 2: Create separate Dockerfiles for Render

Create these files:

**`Dockerfile.backend`** (for Render backend):
```dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel cython && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data models knowledge_base logs

EXPOSE 10000

# Use port from environment, default to 10000 for Render
CMD ["sh", "-c", "uvicorn unified_forecaster_app:app --host 0.0.0.0 --port ${API_PORT:-10000} --workers 1"]
```

**`Dockerfile.frontend`** (for Render frontend):
```dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel cython && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data models knowledge_base logs

EXPOSE 10000

# Use port from environment, default to 10000 for Render
CMD ["sh", "-c", "streamlit run web_app_v2.py --server.port=${STREAMLIT_SERVER_PORT:-10000} --server.address=0.0.0.0 --server.headless=true"]
```

---

## 📝 Quick Setup Checklist

### Backend Setup:
- [ ] Create new Web Service
- [ ] Connect GitHub repo
- [ ] Set name: `forecast-backend`
- [ ] Runtime: Docker
- [ ] Dockerfile: `Dockerfile.backend` (or `Dockerfile`)
- [ ] Set environment variables (API keys, PORT=10000)
- [ ] Deploy and copy URL

### Frontend Setup:
- [ ] Create new Web Service
- [ ] Connect GitHub repo
- [ ] Set name: `forecast-frontend`
- [ ] Runtime: Docker
- [ ] Dockerfile: `Dockerfile.frontend` (or `Dockerfile`)
- [ ] Set environment variables (including BACKEND_URL)
- [ ] Deploy and get URL

---

## 🔄 Update Code for Render Port

We need to update the backend to use port 10000. Let me check the current code and update it.

**Update `unified_forecaster_app.py`:**
```python
# Change this:
API_PORT = int(os.getenv("API_PORT", "8000"))

# To this:
API_PORT = int(os.getenv("API_PORT", "10000"))  # Render default
```

**Update `app_v8.py`:**
Make sure it reads `BACKEND_URL` from environment (already done ✅)

---

## 💰 Free Tier Limits

### Render Free Tier:
- ✅ **750 hours/month** per service (enough for always-on)
- ✅ **512MB RAM** per service
- ✅ **0.1 CPU** per service
- ⚠️ **Spins down after 15 minutes** of inactivity (cold start ~30 seconds)

### Free Tier Tips:
- Keep services active with a ping service (free)
- Or upgrade to Starter ($7/month each) for always-on

---

## 🚀 Deployment Process

1. **Push code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create services in Render** (follow steps above)

3. **Wait for builds** (5-10 minutes first time)

4. **Test your app:**
   - Backend: `https://forecast-backend.onrender.com/health`
   - Frontend: `https://forecast-frontend.onrender.com`

---

## 🔧 Troubleshooting

### Issue: Build fails
- Check build logs in Render dashboard
- Verify Dockerfile path is correct
- Ensure all dependencies are in `requirements.txt`

### Issue: Service won't start
- Check logs in Render dashboard
- Verify environment variables are set
- Ensure port is set to 10000 (not 8000)

### Issue: Frontend can't reach backend
- Verify `BACKEND_URL` is set correctly
- Check backend is deployed and running
- Test backend health endpoint directly

### Issue: Free tier spins down
- This is normal - first request after inactivity takes ~30 seconds
- Consider using a ping service to keep it warm
- Or upgrade to Starter plan for always-on

---

## 📊 Monitoring

- **Logs:** View in Render dashboard for each service
- **Metrics:** CPU, Memory, Response Time in dashboard
- **Deployments:** Auto-deploys on every git push

---

## ✅ Post-Deployment Checklist

- [ ] Backend health check works: `https://forecast-backend.onrender.com/health`
- [ ] Frontend loads: `https://forecast-frontend.onrender.com`
- [ ] Frontend can reach backend (test API call)
- [ ] RAG engine works
- [ ] File upload works
- [ ] Forecasting works
- [ ] Environment variables are set correctly

---

## 🎉 You're Done!

Your app is now live on:
- **Backend:** `https://forecast-backend.onrender.com`
- **Frontend:** `https://forecast-frontend.onrender.com`

**Share your frontend URL with anyone!** 🚀

---

## 📝 Next Steps

1. Test all features
2. Monitor usage (free tier limits)
3. Set up custom domain (optional, paid)
4. Configure auto-deployment from GitHub
5. Set up notifications for deployments

---

## 🔗 Useful Links

- [Render Dashboard](https://dashboard.render.com)
- [Render Docs](https://render.com/docs)
- [Docker on Render](https://render.com/docs/docker)
- [Free Tier Info](https://render.com/docs/free)

---

**Ready to deploy? Let me create the Render-specific Dockerfiles for you!** 🚀

