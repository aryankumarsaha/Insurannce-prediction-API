# Render.com Deployment Guide

## Prerequisites
✅ GitHub repository created and pushed (already done)
✅ Dockerfile configured 
✅ render.yaml configured

## Step-by-Step Deployment

### 1. Create Render Account
- Go to https://render.com
- Click **"Sign Up"**
- Choose **"Sign up with GitHub"** for seamless integration
- Authorize Render to access your GitHub account
- Verify your email

### 2. Connect GitHub Repository
- In Render dashboard, click **"New +"**
- Select **"Web Service"**
- Choose **"Deploy an existing repository"**
- Find and select `aryankumarsaha/Insurannce-prediction-API`
- Click **"Connect"**

### Render (Docker) - Recommended

If you've chosen the Docker environment (recommended), Render will build your image using the `Dockerfile` in the repository. Key notes:

- In the Render UI select **Environment: Docker** when creating the Web Service.
- Leave the **Start Command** blank so Render uses the Dockerfile `CMD` (or paste the inline shell command if the UI requires a value).
- Ensure `render.yaml` is present (optional) and that `dockerfile` points to `./dockerfile`.

Render will run the `CMD` in your `Dockerfile`, which in this project starts both the FastAPI and Streamlit services and reads ports from environment variables.


### 3. Configure Service
The form will appear. Fill in:

| Field | Value |
|-------|-------|
| **Name** | `insurance-prediction-api` |
| **Environment** | `Docker` |
| **Region** | `Oregon` (US) or nearest to you |
| **Branch** | `main` |
| **Dockerfile** | `./dockerfile` |
| **Plan** | `Free` |

### 4. Environment Variables (Optional)
If you want to add the Tableau dashboard URL later:
- Click **"Advanced"**
- Add key-value pairs under **Environment**:
  - `TABLEAU_DASHBOARD_URL`: (your Tableau public URL, if any)

### 5. Deploy
- Click **"Create Web Service"**
- Render will:
  - Build Docker image from your Dockerfile
  - Deploy container to Render infrastructure
  - Assign you a free `.onrender.com` domain
  - Auto-deploy on every GitHub push

### 6. Access Your App
Once deployment completes (5-10 minutes):

| Service | URL |
|---------|-----|
| **FastAPI** | `https://insurance-prediction-api.onrender.com/` |
| **Health Check** | `https://insurance-prediction-api.onrender.com/health` |
| **Streamlit Dashboard** | `https://insurance-prediction-api.onrender.com/` (proxied) |
| **API Docs** | `https://insurance-prediction-api.onrender.com/docs` |

### 7. Test Your Deployment

**API Health Check:**
```bash
curl https://insurance-prediction-api.onrender.com/health
```

**Make a Prediction:**
```bash
curl -X POST https://insurance-prediction-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "weight": 70,
    "height": 1.75,
    "income_lpa": 5.5,
    "smoker": false,
    "city": "Mumbai",
    "occupation": "engineer"
  }'
```

## Free Tier Limits
- **Compute**: 0.5 CPU, 512 MB RAM (may be slow initially)
- **Uptime**: Services spin down after 15 minutes of inactivity
  - First request after sleep may take 30 seconds
  - Subsequent requests will be fast
- **Database**: Not included (your app uses SQLite locally)
- **Auto-deploy**: Included ✅

## Important Notes

### Cold Start Behavior
- First request wakes the service (30 sec wait)
- Subsequent requests are fast
- Use a monitoring service to keep it warm if needed

### Database Persistence
- Each deployment creates a fresh container
- SQLite database resets on each redeploy
- For production, consider Render PostgreSQL add-on (paid)

### Troubleshooting

**Deployment stuck or failed:**
- Check "Logs" tab in Render dashboard
- Verify all files are committed to GitHub
- Ensure Dockerfile paths are correct

**Streamlit not showing:**
- Check Render logs for Python errors
- Ensure `STREAMLIT_SERVER_HEADLESS=true` is set

**Port issues:**
- Render automatically exposes ports 8000 and 8501
- Container maps both services automatically

## Next Steps (Optional)

1. **Set up monitoring**: Use an uptime robot to keep your app warm
2. **Add custom domain**: Render allows custom domains even on free tier
3. **Enable GitHub integration**: Auto-redeploy on code push (already configured)
4. **Upgrade when needed**: Switch from Free → $7/month plan as traffic grows

## Support
- Render Docs: https://render.com/docs
- Common Issues: https://render.com/docs/troubleshooting
