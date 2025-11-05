"""
Test Telegram bot connection
"""
import logging
from telegram_bot import BacBoTelegramBot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_telegram():
    """Test Telegram bot connection and send a test message"""
    print("=" * 50)
    print("Testing Telegram Bot Connection")
    print("=" * 50)
    
    print(f"\nBot Token: {TELEGRAM_BOT_TOKEN[:10]}..." if TELEGRAM_BOT_TOKEN else "Bot Token: NOT SET")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    if not TELEGRAM_BOT_TOKEN:
        print("\n❌ ERROR: TELEGRAM_BOT_TOKEN is not set!")
        print("Please set it in your .env file or config.py")
        return False
    
    if not TELEGRAM_CHAT_ID:
        print("\n❌ ERROR: TELEGRAM_CHAT_ID is not set!")
        print("Please set it in your .env file or config.py")
        return False
    
    try:
        print("\nCreating Telegram bot instance...")
        bot = BacBoTelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        if not bot.bot:
            print("❌ ERROR: Bot instance is None!")
            return False
        
        print("✅ Bot instance created successfully")
        
        # Test sending a simple message
        print("\nSending test message...")
        test_message = "🧪 Test message from Bac Bo Bot!\n\nIf you see this, the bot is working correctly!"
        success = bot.send_message(test_message)
        
        if success:
            print("✅ Test message sent successfully!")
            print("\nPlease check your Telegram - you should see the test message.")
            return True
        else:
            print("❌ Failed to send test message")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_telegram()

