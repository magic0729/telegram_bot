"""
Test script for Bac Bo bot
This script can be used to test individual components
"""
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from scraper import BacBoScraper
from telegram_bot import BacBoTelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_scraper():
    """Test the scraper"""
    logger.info("Testing scraper...")
    scraper = BacBoScraper(url='https://www.vemabet10.com/pt/game/bac-bo/play-for-real', headless=False)
    try:
        scraper.start()
        stats = scraper.get_betting_statistics()
        if stats:
            logger.info(f"Successfully extracted stats: {stats}")
        else:
            logger.warning("Could not extract stats")
    finally:
        scraper.close()


def test_telegram():
    """Test Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not configured")
        return
    
    logger.info("Testing Telegram bot...")
    bot = BacBoTelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Test entry alert
    bot.send_entry_alert(player_percent=82, banker_percent=14, language='pt')
    
    # Test scoreboard
    bot.send_scoreboard(language='pt')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test = sys.argv[1]
        if test == 'scraper':
            test_scraper()
        elif test == 'telegram':
            test_telegram()
        else:
            print("Usage: python test_bot.py [scraper|telegram]")
    else:
        print("Usage: python test_bot.py [scraper|telegram]")
        print("  scraper - Test web scraper")
        print("  telegram - Test Telegram bot")

