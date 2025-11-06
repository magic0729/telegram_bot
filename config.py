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
HEADLESS = False  # Set to False to see browser window (changed for debugging)
WAIT_TIMEOUT = 30  # seconds to wait for elements to load

