"""
Diagnostic script to see what data the bot can actually extract from the page
"""
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import platform

# Set environment variable for Windows 64-bit
if platform.system() == 'Windows':
    os.environ['WDM_OS_TYPE'] = 'win64'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_page():
    """Diagnose what data is available on the page"""
    url = 'https://www.vemabet10.com/pt/game/bac-bo/play-for-real'
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver_manager = ChromeDriverManager()
    driver_path = driver_manager.install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        logger.info(f"Navigating to {url}")
        driver.get(url)
        time.sleep(10)  # Wait for page to load
        
        print("\n" + "="*80)
        print("MAIN PAGE ANALYSIS")
        print("="*80)
        
        # Get page title
        print(f"\nPage Title: {driver.title}")
        
        # Get all text content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"\nBody text length: {len(body_text)} characters")
        print(f"\nFirst 1000 characters of body text:")
        print(body_text[:1000])
        
        # Look for percentages
        import re
        all_percentages = re.findall(r'(\d+)%', body_text)
        print(f"\nFound {len(all_percentages)} percentages in body text: {all_percentages[:20]}")
        
        # Look for keywords
        keywords = ['JOGADOR', 'PLAYER', 'BANCA', 'BANKER', 'EMPATE', 'TIE', '52%', '73%', '40%', '8%']
        found_keywords = []
        for keyword in keywords:
            if keyword in body_text.upper():
                found_keywords.append(keyword)
        print(f"\nFound keywords: {found_keywords}")
        
        # Check for iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\nFound {len(iframes)} iframe(s)")
        
        for idx, iframe in enumerate(iframes):
            print(f"\n" + "="*80)
            print(f"IFRAME {idx + 1} ANALYSIS")
            print("="*80)
            
            try:
                # Get iframe src
                src = iframe.get_attribute('src')
                print(f"\nIframe src: {src}")
                
                # Switch to iframe
                driver.switch_to.frame(iframe)
                time.sleep(3)
                
                # Get iframe content
                iframe_body = driver.find_element(By.TAG_NAME, "body")
                iframe_text = iframe_body.text
                print(f"\nIframe body text length: {len(iframe_text)} characters")
                print(f"\nFirst 1000 characters of iframe text:")
                print(iframe_text[:1000])
                
                # Look for percentages in iframe
                iframe_percentages = re.findall(r'(\d+)%', iframe_text)
                print(f"\nFound {len(iframe_percentages)} percentages in iframe: {iframe_percentages[:20]}")
                
                # Look for keywords in iframe
                iframe_keywords = []
                for keyword in keywords:
                    if keyword in iframe_text.upper():
                        iframe_keywords.append(keyword)
                print(f"\nFound keywords in iframe: {iframe_keywords}")
                
                # Try JavaScript extraction
                try:
                    js_text = driver.execute_script("return document.body.innerText;")
                    print(f"\nJavaScript extracted text length: {len(js_text)} characters")
                    print(f"\nFirst 500 characters:")
                    print(js_text[:500])
                    
                    # Look for percentages in JS text
                    js_percentages = re.findall(r'(\d+)%', js_text)
                    print(f"\nFound {len(js_percentages)} percentages in JS text: {js_percentages[:20]}")
                except Exception as e:
                    print(f"\nJavaScript extraction error: {e}")
                
                # Get page source
                try:
                    page_source = driver.page_source
                    print(f"\nPage source length: {len(page_source)} characters")
                    
                    # Look for specific patterns in source
                    source_percentages = re.findall(r'(\d+)%', page_source)
                    print(f"\nFound {len(source_percentages)} percentages in page source: {source_percentages[:30]}")
                    
                    # Look for patterns like "52%" or "73%"
                    important_percentages = [p for p in source_percentages if int(p.replace('%', '')) > 40 and int(p.replace('%', '')) < 100]
                    print(f"\nImportant percentages (40-100%): {important_percentages[:10]}")
                except Exception as e:
                    print(f"\nPage source extraction error: {e}")
                
                # Switch back
                driver.switch_to.default_content()
                
            except Exception as e:
                print(f"\nError analyzing iframe {idx + 1}: {e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        print("\n" + "="*80)
        print("DIAGNOSIS COMPLETE")
        print("="*80)
        print("\nPress Enter to close browser...")
        input()
        
    except Exception as e:
        logger.error(f"Error during diagnosis: {e}", exc_info=True)
    finally:
        driver.quit()

if __name__ == '__main__':
    diagnose_page()

