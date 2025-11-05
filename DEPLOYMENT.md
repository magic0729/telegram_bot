# Deployment Guide

This guide will help you deploy your Bac Bo Bot so users can interact with it online.

## ⚠️ Important: Platform Choice

**Vercel** (serverless) has limitations:
- ❌ Execution timeout: 10-60 seconds max
- ❌ Cannot run continuous loops
- ❌ Selenium/WebDriver won't work
- ⚠️ Not suitable for this bot

**Railway/Render/Fly.io** (recommended):
- ✅ Supports long-running processes
- ✅ Works with Selenium
- ✅ Persistent state
- ✅ Better for this use case

## Quick Start: Deploy to Railway (Recommended)

### 1. Sign up at [railway.app](https://railway.app)

### 2. Deploy via GitHub

1. Push your code to GitHub
2. Go to Railway → New Project → Deploy from GitHub
3. Select your repository
4. Railway will auto-detect Python and deploy

### 3. Set Environment Variables (Optional)

In Railway → Variables:
- `FLASK_ENV`: `production`
- `TELEGRAM_BOT_TOKEN`: (optional, users can provide via UI)
- `TELEGRAM_CHAT_ID`: (optional, users can provide via UI)

### 4. Access Your Bot

Railway will provide a URL like: `https://your-app.up.railway.app`

Users can now:
1. Visit your URL
2. Enter their Telegram bot token and chat ID
3. Click "Start" to begin monitoring
4. Click "Stop" to stop (sends Telegram message)

## What Was Fixed

✅ **Stop button now sends Telegram message** - When users click stop, a message is sent to Telegram before stopping

✅ **Vercel configuration created** - Files are ready, but Vercel has limitations (see above)

✅ **Railway configuration created** - Better option for this bot

✅ **Production-ready port configuration** - App now uses PORT environment variable

## Files Created

- `vercel.json` - Vercel configuration (has limitations)
- `api/index.py` - Vercel serverless handler
- `Procfile` - Railway/Heroku start command
- `railway.json` - Railway configuration
- `.vercelignore` - Files to exclude from Vercel
- `VERCEL_DEPLOYMENT.md` - Detailed Vercel guide
- `RAILWAY_DEPLOYMENT.md` - Detailed Railway guide

## Testing Locally

Before deploying, test locally:

```bash
python app_ui.py
```

Then visit `http://localhost:8000`

## Next Steps

1. **Deploy to Railway** (recommended)
2. **Test the web UI** with your Telegram credentials
3. **Share the URL** with users
4. **Monitor logs** in Railway dashboard

## Support

For detailed deployment instructions:
- Railway: See `RAILWAY_DEPLOYMENT.md`
- Vercel: See `VERCEL_DEPLOYMENT.md` (not recommended due to limitations)

