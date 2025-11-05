# Fixing Chrome Installation on Railway

The error `'NoneType' object has no attribute 'split'` occurs because Chrome/Chromium is not installed on Railway by default.

## Solution

I've updated the code to:
1. **Better error handling** - Catches the specific error and provides a clear message
2. **Chrome detection** - Automatically detects Chrome version if installed
3. **Multiple installation methods** - Supports different deployment approaches

## Quick Fix: Use Dockerfile (Recommended)

The easiest solution is to use the `Dockerfile` I created. Railway will automatically detect it:

1. **Push the Dockerfile to your repository** (it's already created in the root)
2. **In Railway**, go to your service → **Settings → Build**
3. **Select "Dockerfile"** as the build method (if not auto-detected)
4. **Redeploy**

The Dockerfile includes Chrome installation and all dependencies.

### Alternative: Custom Build Script (If Dockerfile doesn't work)

If Railway doesn't detect the Dockerfile, you can create a build script:

1. Create a file `.railway/build.sh`:
```bash
#!/bin/bash
apt-get update
apt-get install -y wget gnupg ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable
pip install -r requirements.txt
```

2. In Railway settings, set build command to: `bash .railway/build.sh`

## What Changed

### scraper.py
- Added better error handling for ChromeDriverManager
- Added Chrome binary detection for Linux/Railway
- Added explicit Chrome version detection
- Better error messages when Chrome is missing

### Files Created
- `Dockerfile` - Docker image with Chrome pre-installed
- `railway.json` - Updated with Chrome installation in build command
- `nixpacks.toml` - Alternative build configuration
- `railway_setup.sh` - Setup script (optional)

## Testing

After deploying, check Railway logs to see:
- "Using Selenium Manager for ChromeDriver" (best case)
- "Found Chrome binary at: /usr/bin/google-chrome" (if using Dockerfile)
- Or clear error messages if Chrome is still missing

## If Still Not Working

1. **Check Railway logs** - Look for Chrome installation messages
2. **Verify Chrome is installed** - Check if `/usr/bin/google-chrome` exists
3. **Use Dockerfile** - More reliable than build commands
4. **Check Railway environment** - Some Railway plans may have restrictions

## Next Steps

1. Push the updated code to your repository
2. Redeploy on Railway
3. Check logs for Chrome installation
4. Test the bot again

The error should now either:
- Be fixed (Chrome installed successfully)
- Show a clear error message explaining what's missing

