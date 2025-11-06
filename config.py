"""
Configuration file for Bac Bo bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8281858265:AAF0uvXOU3Kzn7z_kJsD4ppGxi3U9QEj6Hk')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '8246955075')

# Website Configuration
BAC_BO_URL = 'https://www.vemabet10.com/pt/game/bac-bo/play-for-real'

# Scraping Configuration
SCRAPE_INTERVAL = 5  # seconds between scraping attempts
PLAYER_WIN_THRESHOLD = 98  # percentage threshold for sending alerts

# Language Configuration
DEFAULT_LANGUAGE = 'en'  # 'en' for English, 'pt' for Portuguese

# Selenium Configuration
# Auto-detect production environment (Railway/Heroku sets PORT env var)
# In production, always use headless mode
_is_production = "PORT" in os.environ or os.environ.get("FLASK_ENV") == "production"
# In production, force headless=True. Otherwise, use HEADLESS env var or default to False
HEADLESS = True if _is_production else (os.getenv("HEADLESS", "False").lower() == "true")
WAIT_TIMEOUT = 30  # seconds to wait for elements to load

# Log configuration for debugging (only import logging if needed)
if _is_production:
    import logging
    logging.info(f"Production mode detected: HEADLESS={HEADLESS}, PORT env exists: {'PORT' in os.environ}")

