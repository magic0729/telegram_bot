"""
Script to fix ChromeDriver cache issues
This will clear the webdriver-manager cache and force a fresh download
"""
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_chromedriver_cache():
    """Clear ChromeDriver cache"""
    cache_path = os.path.join(os.path.expanduser('~'), '.wdm')
    
    if os.path.exists(cache_path):
        logger.info(f"Clearing ChromeDriver cache at: {cache_path}")
        try:
            shutil.rmtree(cache_path, ignore_errors=True)
            logger.info("Cache cleared successfully!")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    else:
        logger.info("No cache found to clear")
        return True

if __name__ == '__main__':
    import sys
    
    auto_run = '--yes' in sys.argv or '-y' in sys.argv
    
    if not auto_run:
        print("This script will clear the ChromeDriver cache to fix architecture issues.")
        print("Press Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)
    
    try:
        if clear_chromedriver_cache():
            print("\nCache cleared! Try running the bot again.")
        else:
            print("\nFailed to clear cache. You may need to manually delete:")
            print(os.path.join(os.path.expanduser('~'), '.wdm'))
    except Exception as e:
        print(f"\nError: {e}")

