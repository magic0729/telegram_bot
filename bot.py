"""
Main bot for monitoring Bac Bo game and sending Telegram alerts
"""
import logging
import time
from typing import Optional
from scraper import BacBoScraper
from telegram_bot import BacBoTelegramBot
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    BAC_BO_URL,
    SCRAPE_INTERVAL,
    PLAYER_WIN_THRESHOLD,
    DEFAULT_LANGUAGE,
    HEADLESS,
    WAIT_TIMEOUT
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for better troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BacBoBot:
    """Main bot class for monitoring Bac Bo game"""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.scraper = BacBoScraper(
            url=BAC_BO_URL,
            headless=HEADLESS,
            wait_timeout=WAIT_TIMEOUT
        )
        # Allow overriding credentials at runtime
        bot_token = token or TELEGRAM_BOT_TOKEN
        bot_chat_id = chat_id or TELEGRAM_CHAT_ID
        self.telegram_bot = BacBoTelegramBot(
            token=bot_token,
            chat_id=bot_chat_id
        )
        self.language = DEFAULT_LANGUAGE
        self.last_stats = None
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds between alerts
        self.last_stats_sent = None  # Track last stats sent to Telegram
        self._stop = False
        
    def _should_send_alert(self, stats: dict) -> bool:
        """Determine if we should send an alert based on stats"""
        if not stats:
            return False
        
        # Check if player percent is above threshold
        if stats.get('player_percent', 0) > PLAYER_WIN_THRESHOLD:
            # Check cooldown to avoid spam
            current_time = time.time()
            if current_time - self.last_alert_time > self.alert_cooldown:
                return True
        
        return False
    
    def _detect_result(self, current_stats: dict, previous_stats: dict) -> Optional[str]:
        """
        Try to detect if there was a win or loss based on stat changes
        This is a heuristic approach - may need adjustment based on actual game behavior
        """
        if not current_stats or not previous_stats:
            return None
        
        # This is a simplified detection - in reality, you'd need to track
        # actual game results from the page
        # For now, we'll just track when alerts are sent
        return None
    
    def run_once(self) -> bool:
        """Run one iteration of monitoring"""
        try:
            # Get current statistics
            stats = self.scraper.get_betting_statistics()
            
            if not stats:
                logger.warning("Could not retrieve betting statistics")
                # Send status update even if stats can't be retrieved
                self.telegram_bot.send_status_update(stats=None, language=self.language)
                return False
            
            logger.info(
                f"Stats - Player: {stats.get('player_percent')}%, "
                f"Banker: {stats.get('banker_percent')}%, "
                f"Tie: {stats.get('tie_percent')}%"
            )
            
            # Send real-time status update periodically
            # Send if stats changed significantly (>3%) or it's been a while
            should_send_update = False
            if not self.last_stats_sent:
                should_send_update = True
            elif abs(stats.get('player_percent', 0) - self.last_stats_sent.get('player_percent', 0)) > 3:
                should_send_update = True
            
            if should_send_update:
                self.telegram_bot.send_status_update(stats=stats, language=self.language)
                self.last_stats_sent = stats.copy()
            
            # Check if we should send an alert
            if self._should_send_alert(stats):
                player_pct = stats.get('player_percent', 0)
                logger.info(f"Player percentage ({player_pct}%) exceeds threshold ({PLAYER_WIN_THRESHOLD}%)")
                
                # Send entry alert
                try:
                    success = self.telegram_bot.send_entry_alert(
                        player_percent=player_pct,
                        banker_percent=stats.get('banker_percent', 0),
                        language=self.language
                    )
                    
                    if success:
                        logger.info("✅ Entry alert sent successfully to Telegram")
                        self.last_alert_time = time.time()
                        self.last_stats = stats.copy()
                        return True
                    else:
                        logger.error("❌ Failed to send entry alert to Telegram")
                except Exception as e:
                    logger.error(f"Error sending entry alert: {e}", exc_info=True)
            
            # Update last stats
            self.last_stats = stats.copy()
            return True
            
        except Exception as e:
            logger.error(f"Error in run_once: {e}", exc_info=True)
            # Send error notification
            try:
                self.telegram_bot.send_message(f"⚠️ Error in monitoring cycle: {str(e)[:100]}")
            except:
                pass
            return False
    
    def run(self):
        """Main run loop"""
        logger.info("Starting Bac Bo monitoring bot...")
        
        # Check Telegram bot first
        if not self.telegram_bot.bot:
            logger.error("Telegram bot not properly configured. Please check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return
        
        # Send startup message
        try:
            self.telegram_bot.send_startup_message(language=self.language)
            logger.info("Startup message sent to Telegram")
        except Exception as e:
            logger.warning(f"Failed to send startup message: {e}")
        
        # Initialize scraper
        try:
            self.scraper.start()
            logger.info("Scraper initialized successfully")
            
            # Send confirmation that site is opened
            try:
                self.telegram_bot.send_message("✅ Site opened successfully! Bot is now monitoring the game.")
                logger.info("Site opened confirmation sent")
            except Exception as e:
                logger.warning(f"Failed to send site opened message: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            try:
                self.telegram_bot.send_message(f"❌ Failed to initialize scraper: {str(e)[:200]}")
            except:
                pass
            return
        
        logger.info("Bot is running. Monitoring Bac Bo game...")
        logger.info(f"Alert threshold: Player > {PLAYER_WIN_THRESHOLD}%")
        logger.info(f"Scrape interval: {SCRAPE_INTERVAL} seconds")
        
        iteration_count = 0
        last_status_update = 0
        status_update_interval = 30  # Send status update every 30 seconds
        
        try:
            while not self._stop:
                iteration_count += 1
                current_time = time.time()
                
                # Run monitoring cycle
                self.run_once()
                
                # Send periodic status update (every minute)
                if current_time - last_status_update >= status_update_interval:
                    try:
                        if self.last_stats:
                            self.telegram_bot.send_status_update(stats=self.last_stats, language=self.language)
                        else:
                            self.telegram_bot.send_status_update(stats=None, language=self.language)
                        last_status_update = current_time
                        logger.info(f"Sent periodic status update (iteration {iteration_count})")
                    except Exception as e:
                        logger.warning(f"Failed to send periodic status update: {e}")
                
                time.sleep(SCRAPE_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            # Send message immediately before cleanup
            try:
                self.telegram_bot.send_message("🛑 Bot stopped by user (KeyboardInterrupt)")
                time.sleep(1)  # Give message time to send
            except Exception as e:
                logger.error(f"Error sending stop message: {e}")
        except Exception as e:
            logger.error(f"Fatal error in run loop: {e}", exc_info=True)
            # Send error message immediately
            try:
                self.telegram_bot.send_message(f"❌ Fatal error: {str(e)[:200]}")
                time.sleep(1)
            except Exception as e2:
                logger.error(f"Error sending error message: {e2}")
        finally:
            # Always try to send shutdown message, even if there were errors
            # Use a separate thread to ensure message is sent even if event loop is closing
            import threading
            
            def send_shutdown():
                try:
                    shutdown_sent = self.telegram_bot.send_shutdown_message(language=self.language)
                    if shutdown_sent:
                        logger.info("✅ Shutdown message sent to Telegram")
                    else:
                        logger.warning("⚠️ Shutdown message send returned False")
                        # Try simple message
                        try:
                            self.telegram_bot.send_message("🛑 Bot stopped")
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Failed to send shutdown message: {e}")
                    # Try one more time with a simple message
                    try:
                        self.telegram_bot.send_message("🛑 Bot stopped")
                    except:
                        pass
            
            # Send shutdown message in a separate thread to avoid blocking
            shutdown_thread = threading.Thread(target=send_shutdown, daemon=False)
            shutdown_thread.start()
            shutdown_thread.join(timeout=5)  # Wait max 5 seconds for message to send
            
            # Close scraper after sending messages
            try:
                self.scraper.close()
                logger.info("Scraper closed")
            except Exception as e:
                logger.error(f"Error closing scraper: {e}")
            
            logger.info("Bot shutdown complete")

    def stop(self):
        """Signal the bot to stop gracefully"""
        self._stop = True

    def status(self) -> dict:
        """Return a lightweight status snapshot"""
        return {
            'running': not self._stop,
            'last_stats': self.last_stats or {},
            'alert_threshold': PLAYER_WIN_THRESHOLD,
            'scrape_interval': SCRAPE_INTERVAL
        }


def main():
    """Main entry point"""
    bot = BacBoBot()
    bot.run()


if __name__ == '__main__':
    main()

