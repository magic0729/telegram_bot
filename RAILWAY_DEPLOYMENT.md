# Railway Deployment Guide (Recommended)

Railway is **recommended** for this bot because it supports:
- ✅ Long-running processes (continuous monitoring loop)
- ✅ Selenium/WebDriver (browser automation)
- ✅ Background threads
- ✅ Persistent state
- ✅ Free tier available

## Quick Deploy

### Option 1: Deploy via Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Initialize and Deploy**:
   ```bash
   railway init
   railway up
   ```

### Option 2: Deploy via GitHub (Easiest)

1. **Push your code to GitHub** (if not already done)

2. **Go to Railway**:
   - Visit [railway.app](https://railway.app)
   - Sign up/login with GitHub

3. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

4. **Configure**:
   - Railway will auto-detect Python
   - It will use the `Procfile` for the start command
   - Or manually set: `python app_ui.py`

5. **Set Environment Variables** (Optional):
   - Go to Variables tab
   - Add if needed:
     - `TELEGRAM_BOT_TOKEN`: Your default bot token
     - `TELEGRAM_CHAT_ID`: Your default chat ID
     - `FLASK_ENV`: `production`

6. **Deploy**:
   - Railway will automatically deploy
   - Your app will be available at: `https://your-app-name.up.railway.app`

## Environment Variables

Set these in Railway dashboard → Variables:

- `TELEGRAM_BOT_TOKEN` (optional): Default bot token
- `TELEGRAM_CHAT_ID` (optional): Default chat ID
- `FLASK_ENV`: Set to `production` for production
- `PORT`: Automatically set by Railway (don't override)

**Note**: Users can provide their own bot token and chat ID via the web UI, so global env vars are optional.

## How It Works

1. **Users visit your Railway URL**
2. **They enter their Telegram bot token and chat ID** in the web UI
3. **They click "Start"** to begin monitoring
4. **The bot runs continuously** in a background thread
5. **Users can click "Stop"** to stop monitoring (sends Telegram message)

## Custom Domain (Optional)

1. Go to Settings → Networking
2. Generate a domain or add your custom domain
3. Railway will provide SSL certificates automatically

## Monitoring

- **Logs**: View logs in Railway dashboard
- **Metrics**: Railway provides basic metrics
- **Deployments**: All deployments are tracked

## Troubleshooting

### Bot not starting?
- Check logs in Railway dashboard
- Verify Selenium/Chrome dependencies (Railway should handle this)
- Check that PORT is set (Railway sets this automatically)

### Telegram messages not sending?
- Verify bot token is correct
- Verify chat ID is correct
- Check that your Telegram bot is running
- Check Railway logs for errors

### Bot stops after a few minutes?
- Check Railway logs for errors
- Verify you're on a paid plan (free tier has limitations)
- Check if there are memory/CPU limits being hit

## Cost

- **Free tier**: $5/month credit
- **Hobby plan**: $5/month (includes $5 credit)
- **Pro plan**: $20/month (more resources)

The bot should run fine on the free/hobby tier for moderate usage.

## Next Steps

1. Deploy to Railway
2. Test the web UI
3. Test starting/stopping the bot
4. Verify Telegram messages are sent
5. Share the URL with users!

## Support

If you encounter issues:
1. Check Railway logs
2. Check application logs
3. Verify environment variables
4. Contact Railway support

