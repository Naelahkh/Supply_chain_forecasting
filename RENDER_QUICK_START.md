# ⚡ Render Quick Start - 5 Minutes!

## ✅ Prerequisites
- GitHub repo with your code ✅
- Render account (sign up at [render.com](https://render.com))

---

## 🚀 Deploy in 3 Steps

### Step 1: Deploy Backend (2 minutes)

1. Go to [render.com](https://render.com) → Sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo: `Naelahkh/Supply_chain_forecasting`
4. **Configure:**
   - **Name:** `forecast-backend`
   - **Dockerfile Path:** `Dockerfile.backend`
   - **Instance:** Free tier
5. **Environment Variables:**
   ```
   GOOGLE_API_KEY=your_key
   HUGGINGFACEHUB_API_TOKEN=your_token
   ```
6. Click **"Create Web Service"** → Wait 5-10 minutes
7. **Copy the URL:** `https://forecast-backend-xxxx.onrender.com`

### Step 2: Deploy Frontend (2 minutes)

1. Click **"New +"** → **"Web Service"**
2. Connect same GitHub repo
3. **Configure:**
   - **Name:** `forecast-frontend`
   - **Dockerfile Path:** `Dockerfile.frontend`
   - **Instance:** Free tier
4. **Environment Variables:**
   ```
   GOOGLE_API_KEY=your_key
   HUGGINGFACEHUB_API_TOKEN=your_token
   BACKEND_URL=https://forecast-backend-xxxx.onrender.com
   ```
   ⚠️ **Use the backend URL from Step 1!**
5. Click **"Create Web Service"** → Wait 5-10 minutes

### Step 3: Test! 🎉

1. Open frontend URL: `https://forecast-frontend-xxxx.onrender.com`
2. Test the app!

---

## 🔍 Verify Everything Works

**Backend Health:**
```
https://forecast-backend-xxxx.onrender.com/health
```

**Frontend:**
```
https://forecast-frontend-xxxx.onrender.com
```

---

## 💡 Pro Tips

- **Free tier spins down** after 15 min inactivity (cold start ~30 sec)
- **Auto-deploys** on every git push
- **HTTPS** included automatically
- **Logs** available in dashboard

---

## 🆘 Troubleshooting

**Build fails?**
- Check Dockerfile path: `Dockerfile.backend` or `Dockerfile.frontend`
- Check build logs in Render dashboard

**Frontend can't reach backend?**
- Verify `BACKEND_URL` is correct
- Test backend `/health` endpoint directly

**Service won't start?**
- Check logs in Render dashboard
- Verify all environment variables are set

---

## 📚 Full Guide

See `RENDER_DEPLOYMENT_GUIDE.md` for detailed instructions.

---

**That's it! Your app is live on Render! 🚀**

