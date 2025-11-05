# Vercel Deployment Guide

## ⚠️ Important Limitations

**Vercel is a serverless platform with execution time limits:**
- **Free tier**: 10 seconds per function execution
- **Pro tier**: 60 seconds per function execution

**Your bot runs a continuous monitoring loop**, which is incompatible with serverless functions. The bot needs to run continuously to monitor the game, but Vercel functions are designed for short-lived requests.

## Current Architecture Issues

The current bot implementation:
- Runs a continuous `while` loop that monitors the game every 5 seconds
- Uses Selenium WebDriver (requires a browser instance)
- Needs to maintain state across multiple iterations

This **cannot run on Vercel** as-is because:
1. Serverless functions timeout after 10-60 seconds
2. Selenium requires persistent browser instances (not available in serverless)
3. Long-running processes are not supported

## Deployment Options

### Option 1: Deploy Web UI Only on Vercel (Recommended)

Deploy just the web interface on Vercel, and run the bot on a different platform:

1. **Web UI on Vercel**: Deploy `app_ui.py` to Vercel for the user interface
2. **Bot on Railway/Render/Fly.io**: Run the actual bot (`bot.py`) on a platform that supports long-running processes

**Platforms that support long-running processes:**
- **Railway** (recommended): Easy deployment, supports Docker
- **Render**: Free tier available, supports web services
- **Fly.io**: Good for Docker-based deployments
- **Heroku**: Paid plans available
- **DigitalOcean App Platform**: Affordable option

### Option 2: Refactor for Serverless (Complex)

You would need to:
1. Replace Selenium with a headless browser service (like Browserless.io or Puppeteer on another service)
2. Use Vercel Cron Jobs to trigger periodic checks
3. Store state in a database (Vercel Postgres, Supabase, etc.)
4. Refactor the monitoring loop to be triggered by cron jobs

This is significantly more complex and may not be cost-effective.

### Option 3: Hybrid Approach

1. Deploy the web UI on Vercel
2. Use the web UI to trigger a bot instance on Railway/Render
3. The bot runs continuously on Railway/Render
4. The web UI communicates with the bot via API

## Deployment Steps (Web UI on Vercel)

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Deploy

```bash
vercel
```

Follow the prompts. For production deployment:

```bash
vercel --prod
```

### 4. Set Environment Variables

In Vercel dashboard, go to your project → Settings → Environment Variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID (optional, users can provide their own)

**Note**: Since users provide their own tokens via the web UI, you may not need to set these globally.

### 5. Limitations with Current Setup

Even deploying the web UI on Vercel has limitations:

1. **Threading**: The bot runs in a background thread, which may not persist between serverless invocations
2. **State**: The `_bot_instance` global variable won't persist across different serverless function invocations
3. **Browser/Selenium**: Selenium requires a browser, which won't work in serverless

## Recommended Solution: Deploy Bot on Railway

### Step 1: Deploy Bot on Railway

1. Create a `Procfile` for Railway:
   ```
   web: python app_ui.py
   ```

2. Or use Railway's Python detection (it will auto-detect `app_ui.py`)

3. Deploy to Railway:
   - Sign up at [railway.app](https://railway.app)
   - Create a new project
   - Connect your GitHub repository
   - Railway will auto-detect Python and deploy

### Step 2: (Optional) Deploy Web UI on Vercel

If you want a separate web UI:
1. The web UI can be deployed on Vercel
2. It can make API calls to your Railway-deployed bot
3. Or users can access the bot directly via Railway URL

## Alternative: Keep Everything on Railway

**Easiest solution**: Deploy everything on Railway:
- Railway supports long-running processes
- No threading/state issues
- Selenium works (they provide containers with browsers)
- One deployment, simpler architecture

## Files Included for Vercel

- `vercel.json`: Vercel configuration
- `api/index.py`: Serverless function handler
- `.vercelignore`: Files to exclude from deployment

## Testing Locally with Vercel

```bash
vercel dev
```

This will run a local server that mimics Vercel's serverless environment.

## Next Steps

1. **For immediate deployment**: Use Railway or Render for the full bot
2. **For Vercel**: Consider refactoring to use cron jobs + external browser service
3. **For production**: Consider the hybrid approach with separate services

## Questions?

If you need help with Railway deployment or refactoring for serverless, let me know!

