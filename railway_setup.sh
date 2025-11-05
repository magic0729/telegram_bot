#!/bin/bash
# Railway setup script - installs Chrome for Selenium

# This script should be run during Railway build process
# Add this to your Railway build command or use it as a build script

echo "🚀 Starting Railway setup for Chrome/Selenium..."

# Check if we're on Railway (has RAILWAY_ENVIRONMENT variable)
if [ -z "$RAILWAY_ENVIRONMENT" ]; then
    echo "⚠️  Not running on Railway, skipping Chrome installation"
    exit 0
fi

# Install Chrome using apt-get (Railway uses Ubuntu-based images)
apt-get update -qq
apt-get install -y -qq \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils

# Install Google Chrome
if ! command -v google-chrome &> /dev/null; then
    echo "📦 Installing Google Chrome..."
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 2>/dev/null
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update -qq
    apt-get install -y -qq google-chrome-stable
fi

# Verify installation
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome installed successfully:"
    google-chrome --version
else
    echo "❌ Chrome installation failed!"
    exit 1
fi

echo "✅ Railway setup complete!"

