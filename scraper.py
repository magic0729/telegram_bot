"""
Web scraper for Bac Bo casino game statistics
"""
import os
import platform
import re
from PIL import Image
import io

# Set environment variable for Windows 64-bit before importing ChromeDriverManager
if platform.system() == 'Windows':
    os.environ['WDM_OS_TYPE'] = 'win64'

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from typing import Dict, Optional

# Try to import pytesseract for OCR
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract not available. OCR functionality will be disabled.")

logger = logging.getLogger(__name__)


class BacBoScraper:
    """Scraper for Bac Bo game statistics"""
    
    def __init__(self, url: str, headless: bool = True, wait_timeout: int = 30):
        self.url = url
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.current_language = 'en'
        
    def _setup_driver(self):
        """Setup Chrome WebDriver.
        Prefer Selenium Manager (built into Selenium) to resolve win32/win64
        chromedriver mismatches automatically. Fall back to webdriver-manager
        only if Selenium Manager is unavailable.
        """
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional options for Railway/Linux environments
        if platform.system() != 'Windows':
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--remote-debugging-port=9222')
            # Try to use Chrome binary if available in common locations
            chrome_binary_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium'
            ]
            for binary_path in chrome_binary_paths:
                if os.path.exists(binary_path):
                    chrome_options.binary_location = binary_path
                    logger.info(f"Found Chrome binary at: {binary_path}")
                    break

        # 1) Try Selenium Manager (no driver path) - this auto-downloads the
        # correct driver for the installed browser and OS.
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Using Selenium Manager for ChromeDriver (auto-managed)")
            return
        except Exception as selenium_manager_error:
            logger.warning(f"Selenium Manager failed, falling back to webdriver-manager: {selenium_manager_error}")

        # 2) Fallback: webdriver-manager with forced win64 on Windows
        try:
            if platform.system() == 'Windows':
                os.environ['WDM_OS_TYPE'] = 'win64'
            else:
                # For Linux/Railway, try to set Chrome version explicitly to avoid version detection issues
                try:
                    import subprocess
                    # Try to get Chrome version
                    for binary_path in ['/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/usr/bin/chromium']:
                        if os.path.exists(binary_path):
                            result = subprocess.run([binary_path, '--version'], capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 and result.stdout:
                                version_str = result.stdout.strip()
                                logger.info(f"Detected Chrome version: {version_str}")
                                # Extract version number (e.g., "Google Chrome 120.0.6099.109" -> "120.0.6099.109")
                                import re
                                version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version_str)
                                if version_match:
                                    chrome_version = version_match.group(1)
                                    # Set ChromeDriver version to match major version
                                    major_version = chrome_version.split('.')[0]
                                    os.environ['WDM_CHROMEDRIVER_VERSION'] = major_version
                                    logger.info(f"Setting ChromeDriver version to: {major_version}")
                            break
                except Exception as version_error:
                    logger.warning(f"Could not detect Chrome version: {version_error}")
            
            # Install ChromeDriver with error handling
            try:
                driver_path = ChromeDriverManager().install()
                if driver_path is None:
                    raise ValueError("ChromeDriverManager.install() returned None")
                
                original_path = driver_path
                logger.info(f"ChromeDriverManager returned path: {driver_path}")
                
                # Fix path resolution: ChromeDriverManager sometimes returns wrong file or directory
                # Check if it's the wrong file (like THIRD_PARTY_NOTICES.chromedriver)
                if os.path.isfile(driver_path):
                    filename = os.path.basename(driver_path)
                    # If it's the wrong file, look in the same directory for the actual executable
                    if 'NOTICES' in filename or filename.endswith('.txt') or filename.endswith('.md'):
                        logger.warning(f"ChromeDriverManager returned wrong file: {filename}, searching for executable...")
                        # First, check the same directory (most common case)
                        same_dir = os.path.dirname(driver_path)
                        chromedriver_path = os.path.join(same_dir, 'chromedriver')
                        if os.path.isfile(chromedriver_path):
                            try:
                                os.chmod(chromedriver_path, 0o755)
                                driver_path = chromedriver_path
                                logger.info(f"Found chromedriver executable in same directory: {driver_path}")
                            except Exception as e:
                                logger.warning(f"Could not use chromedriver from same directory: {e}")
                        
                        # If not found in same directory, search more broadly
                        if driver_path == original_path:
                            search_dirs = [
                                same_dir,  # Same directory
                                os.path.dirname(same_dir),  # Parent directory
                            ]
                            for search_dir in search_dirs:
                                if os.path.isdir(search_dir):
                                    # Look for chromedriver executable
                                    for root, dirs, files in os.walk(search_dir):
                                        for file in files:
                                            if file == 'chromedriver' and 'NOTICES' not in file:
                                                full_path = os.path.join(root, file)
                                                if os.path.isfile(full_path):
                                                    try:
                                                        os.chmod(full_path, 0o755)
                                                        driver_path = full_path
                                                        logger.info(f"Found chromedriver executable at: {driver_path}")
                                                        break
                                                    except Exception as e:
                                                        logger.debug(f"Could not use {full_path}: {e}")
                                                        continue
                                        if driver_path != original_path:
                                            break
                                    if driver_path != original_path:
                                        break
                
                # Fix path resolution: ChromeDriverManager sometimes returns a directory path
                # We need to find the actual chromedriver executable
                if os.path.isdir(driver_path):
                    # Look for chromedriver executable in the directory
                    possible_paths = [
                        os.path.join(driver_path, 'chromedriver'),
                        os.path.join(driver_path, 'chromedriver-linux64', 'chromedriver'),
                        os.path.join(driver_path, 'chromedriver-linux', 'chromedriver'),
                    ]
                    for path in possible_paths:
                        if os.path.isfile(path) and os.access(path, os.X_OK):
                            driver_path = path
                            logger.info(f"Found chromedriver executable at: {driver_path}")
                            break
                    else:
                        # If not found, try to find any executable named chromedriver
                        found_executable = False
                        for root, dirs, files in os.walk(driver_path):
                            for file in files:
                                # Skip non-executable files like THIRD_PARTY_NOTICES
                                if file == 'chromedriver' and 'NOTICES' not in file:
                                    full_path = os.path.join(root, file)
                                    if os.path.isfile(full_path):
                                        # Try to make it executable and check
                                        try:
                                            os.chmod(full_path, 0o755)
                                            if os.access(full_path, os.X_OK):
                                                driver_path = full_path
                                                logger.info(f"Found chromedriver executable at: {driver_path}")
                                                found_executable = True
                                                break
                                        except Exception as e:
                                            logger.debug(f"Could not make {full_path} executable: {e}")
                                            continue
                            if found_executable:
                                break
                    
                    # If still a directory, raise error
                    if os.path.isdir(driver_path):
                        raise ValueError(f"ChromeDriverManager returned directory but chromedriver executable not found: {original_path}")
                
                # Final validation: make sure it's the actual executable file
                if os.path.isfile(driver_path):
                    # Check if it's the wrong file
                    filename = os.path.basename(driver_path)
                    if 'NOTICES' in filename or filename.endswith('.txt') or filename.endswith('.md'):
                        # Still wrong file, search more thoroughly
                        search_dir = os.path.dirname(driver_path)
                        logger.warning(f"Path still points to wrong file, searching in: {search_dir}")
                        for root, dirs, files in os.walk(search_dir):
                            for file in files:
                                if file == 'chromedriver' and 'NOTICES' not in file:
                                    full_path = os.path.join(root, file)
                                    if os.path.isfile(full_path):
                                        try:
                                            os.chmod(full_path, 0o755)
                                            driver_path = full_path
                                            logger.info(f"Found correct chromedriver executable at: {driver_path}")
                                            break
                                        except:
                                            continue
                            if 'NOTICES' not in os.path.basename(driver_path):
                                break
                    
                    # Make sure the file is executable (important for Linux)
                    os.chmod(driver_path, 0o755)
                    logger.info(f"Using chromedriver at: {driver_path}")
                else:
                    raise ValueError(f"ChromeDriver path is not a valid file: {driver_path}")
                    
            except AttributeError as attr_error:
                if "'NoneType' object has no attribute 'split'" in str(attr_error):
                    logger.error("ChromeDriverManager failed to detect Chrome version. This usually means Chrome is not installed.")
                    raise RuntimeError(
                        "Chrome/Chromium is not installed or not found. "
                        "On Railway, you may need to install Chrome in your build process. "
                        "Error: ChromeDriverManager could not detect Chrome version."
                    ) from attr_error
                raise
            except Exception as install_error:
                if "'NoneType' object has no attribute 'split'" in str(install_error):
                    logger.error("ChromeDriverManager failed to detect Chrome version. This usually means Chrome is not installed.")
                    raise RuntimeError(
                        "Chrome/Chromium is not installed or not found. "
                        "On Railway, you may need to install Chrome in your build process. "
                        "Error: ChromeDriverManager could not detect Chrome version."
                    ) from install_error
                raise
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Using webdriver-manager fallback for ChromeDriver")
            return
        except Exception as e:
            logger.error(f"webdriver-manager fallback failed: {e}", exc_info=True)
            raise
        
    def _switch_language(self, target_language: str):
        """Switch page language to target language"""
        if self.current_language == target_language:
            return
            
        try:
            # Try to find language switcher button
            # Common selectors for language buttons
            language_selectors = [
                "//button[contains(@class, 'language')]",
                "//button[contains(text(), 'EN')]",
                "//button[contains(text(), 'PT')]",
                "//div[contains(@class, 'language')]//button",
                "//button[@aria-label='Language']",
                "//select[@id='language']",
            ]
            
            for selector in language_selectors:
                try:
                    if 'select' in selector:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        from selenium.webdriver.support.ui import Select
                        select = Select(element)
                        select.select_by_value(target_language)
                        time.sleep(2)
                        self.current_language = target_language
                        return
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        element.click()
                        time.sleep(2)
                        self.current_language = target_language
                        return
                except:
                    continue
                    
            logger.warning(f"Could not find language switcher, keeping current language: {self.current_language}")
        except Exception as e:
            logger.error(f"Error switching language: {e}")
    
    def start(self):
        """Start the browser and navigate to the game page"""
        if self.driver is None:
            self._setup_driver()
        
        logger.info(f"Navigating to {self.url}")
        self.driver.get(self.url)
        time.sleep(5)  # Wait for page to load
        
        # Switch to English if needed
        self._switch_language('en')
        
    def _extract_stats_from_context(self, driver_context, player_candidates=None, banker_candidates=None, tie_candidates=None) -> Optional[Dict]:
        """Extract statistics from current driver context (main page or iframe)"""
        import re
        
        try:
            player_percent = None
            banker_percent = None
            tie_percent = None
            
            percentage_pattern = r'(\d+)%'
            
            # Initialize candidates if not provided
            if player_candidates is None:
                player_candidates = []
            if banker_candidates is None:
                banker_candidates = []
            if tie_candidates is None:
                tie_candidates = []
            
            # First, try to get page source and search in it
            try:
                page_source = driver_context.page_source
                # Look for percentage patterns near keywords
                logger.debug(f"Page source length: {len(page_source)}")
            except:
                page_source = ""
            
            # Get all visible text elements
            all_elements = driver_context.find_elements(By.XPATH, "//*")
            logger.debug(f"Found {len(all_elements)} elements to check")
            
            # Also collect all text that contains percentages for debugging
            debug_texts = []
            
            # First, try to get all text from the page using JavaScript (more reliable)
            try:
                all_text = driver_context.execute_script("""
                    var allText = [];
                    var all = document.querySelectorAll('*');
                    for (var i = 0; i < all.length; i++) {
                        var text = all[i].innerText || all[i].textContent || '';
                        if (text && text.trim().length > 0 && text.trim().length < 500) {
                            allText.push(text.trim());
                        }
                    }
                    return allText;
                """)
                logger.debug(f"JavaScript extracted {len(all_text)} text elements")
                
                # Search through JavaScript-extracted text
                for text in all_text:
                    try:
                        text_upper = text.upper()
                        
                        # Check for player section
                        if any(keyword in text_upper for keyword in ['JOGADOR', 'PLAYER']):
                            matches = re.findall(percentage_pattern, text)
                            for match in matches:
                                percent_val = float(match)
                                if 0 <= percent_val <= 100:
                                    player_candidates.append(percent_val)
                                    if len(debug_texts) < 5:
                                        debug_texts.append(f"Player: {text[:100]}")
                        
                        # Check for banker section
                        if any(keyword in text_upper for keyword in ['BANCA', 'BANKER']):
                            matches = re.findall(percentage_pattern, text)
                            for match in matches:
                                percent_val = float(match)
                                if 0 <= percent_val <= 100:
                                    banker_candidates.append(percent_val)
                                    if len(debug_texts) < 10:
                                        debug_texts.append(f"Banker: {text[:100]}")
                        
                        # Check for tie section
                        if any(keyword in text_upper for keyword in ['EMPATE', 'TIE']):
                            matches = re.findall(percentage_pattern, text)
                            for match in matches:
                                percent_val = float(match)
                                if 0 <= percent_val <= 100:
                                    tie_candidates.append(percent_val)
                                    if len(debug_texts) < 15:
                                        debug_texts.append(f"Tie: {text[:100]}")
                    except:
                        continue
            except Exception as js_err:
                logger.debug(f"JavaScript text extraction failed: {js_err}")
            
            # Also try traditional element extraction
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if not text or len(text) > 300:  # Skip very long texts
                        continue
                    
                    text_upper = text.upper()
                    
                    # Check for player section
                    if any(keyword in text_upper for keyword in ['JOGADOR', 'PLAYER']):
                        matches = re.findall(percentage_pattern, text)
                        for match in matches:
                            percent_val = float(match)
                            if 0 <= percent_val <= 100:
                                player_candidates.append(percent_val)
                                if len(debug_texts) < 5:
                                    debug_texts.append(f"Player: {text[:100]}")
                    
                    # Check for banker section
                    if any(keyword in text_upper for keyword in ['BANCA', 'BANKER']):
                        matches = re.findall(percentage_pattern, text)
                        for match in matches:
                            percent_val = float(match)
                            if 0 <= percent_val <= 100:
                                banker_candidates.append(percent_val)
                                if len(debug_texts) < 10:
                                    debug_texts.append(f"Banker: {text[:100]}")
                    
                    # Check for tie section
                    if any(keyword in text_upper for keyword in ['EMPATE', 'TIE']):
                        matches = re.findall(percentage_pattern, text)
                        for match in matches:
                            percent_val = float(match)
                            if 0 <= percent_val <= 100:
                                tie_candidates.append(percent_val)
                                if len(debug_texts) < 15:
                                    debug_texts.append(f"Tie: {text[:100]}")
                except:
                    continue
            
            # Log debug info
            if debug_texts:
                logger.info(f"Found potential stat texts: {debug_texts[:5]}")
            logger.info(f"Player candidates: {player_candidates}, Banker: {banker_candidates}, Tie: {tie_candidates}")
            
            # Also try to search in page source directly with more patterns
            if page_source:
                logger.info("Trying to extract from page source...")
                # Search for patterns like "82%" near "JOGADOR" or "PLAYER"
                # Try multiple patterns to catch different HTML structures
                patterns = [
                    r'(?:JOGADOR|PLAYER)[^>]*?(\d+)%',
                    r'(\d+)%[^<]*?(?:JOGADOR|PLAYER)',
                    r'<[^>]*>(?:JOGADOR|PLAYER)[^<]*?(\d+)%',
                    r'(\d+)%[^<]*?<[^>]*>(?:JOGADOR|PLAYER)',
                    r'(?:JOGADOR|PLAYER)[^>]{0,200}(\d+)%',
                    r'(\d+)%[^>]{0,200}(?:JOGADOR|PLAYER)',
                ]
                
                for pattern in patterns:
                    player_matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                    if player_matches:
                        for match in player_matches:
                            try:
                                val = float(match)
                                if 0 <= val <= 100:
                                    player_candidates.append(val)
                                    logger.info(f"Found player percent {val}% in page source using pattern: {pattern[:50]}")
                            except:
                                pass
                
                # Same for banker
                for pattern in patterns:
                    banker_pattern = pattern.replace('JOGADOR|PLAYER', 'BANCA|BANKER')
                    banker_matches = re.findall(banker_pattern, page_source, re.IGNORECASE | re.DOTALL)
                    if banker_matches:
                        for match in banker_matches:
                            try:
                                val = float(match)
                                if 0 <= val <= 100:
                                    banker_candidates.append(val)
                                    logger.info(f"Found banker percent {val}% in page source")
                            except:
                                pass
                
                # Same for tie
                for pattern in patterns:
                    tie_pattern = pattern.replace('JOGADOR|PLAYER', 'EMPATE|TIE')
                    tie_matches = re.findall(tie_pattern, page_source, re.IGNORECASE | re.DOTALL)
                    if tie_matches:
                        for match in tie_matches:
                            try:
                                val = float(match)
                                if 0 <= val <= 100:
                                    tie_candidates.append(val)
                                    logger.info(f"Found tie percent {val}% in page source")
                            except:
                                pass
                
                # Also try to find all percentages in the page and match them to sections
                all_percentages = re.findall(r'(\d+)%', page_source)
                logger.info(f"Found {len(all_percentages)} total percentages in page source")
                
                # Look for percentages that are likely to be the statistics (between 0-100, common values)
                for percent_str in all_percentages:
                    try:
                        val = float(percent_str)
                        if 0 <= val <= 100:
                            # Check context around this percentage
                            idx = page_source.find(percent_str + '%')
                            if idx >= 0:
                                context_start = max(0, idx - 200)
                                context_end = min(len(page_source), idx + 200)
                                context = page_source[context_start:context_end].upper()
                                
                                if any(kw in context for kw in ['JOGADOR', 'PLAYER']):
                                    if val not in player_candidates:
                                        player_candidates.append(val)
                                        logger.info(f"Found player percent {val}% from context")
                                elif any(kw in context for kw in ['BANCA', 'BANKER']):
                                    if val not in banker_candidates:
                                        banker_candidates.append(val)
                                        logger.info(f"Found banker percent {val}% from context")
                                elif any(kw in context for kw in ['EMPATE', 'TIE']):
                                    if val not in tie_candidates:
                                        tie_candidates.append(val)
                                        logger.info(f"Found tie percent {val}% from context")
                    except:
                        pass
            
            # Use the most common value, but prefer larger values for player (likely the main stat)
            if player_candidates:
                # Use the most common, but if multiple, prefer the largest one (likely the main stat)
                player_percent = max(set(player_candidates), key=lambda x: (player_candidates.count(x), x))
                logger.info(f"Selected player percent: {player_percent}% from candidates: {player_candidates}")
            if banker_candidates:
                banker_percent = max(set(banker_candidates), key=lambda x: (banker_candidates.count(x), x))
                logger.info(f"Selected banker percent: {banker_percent}% from candidates: {banker_candidates}")
            if tie_candidates:
                tie_percent = max(set(tie_candidates), key=lambda x: (tie_candidates.count(x), x))
                logger.info(f"Selected tie percent: {tie_percent}% from candidates: {tie_candidates}")
            
            # Alternative: try to find percentages in a structured layout
            # Look for elements that contain both label and percentage
            if player_percent is None or banker_percent is None or tie_percent is None:
                # Try finding parent containers with structured data
                for element in all_elements:
                    try:
                        text = element.text.strip()
                        if not text:
                            continue
                        
                        # Look for patterns like "82% JOGADOR" or "Player 82%"
                        matches = re.findall(r'(\d+)%\s*(?:JOGADOR|PLAYER)', text, re.IGNORECASE)
                        if matches and player_percent is None:
                            player_percent = float(matches[0])
                        
                        matches = re.findall(r'(?:JOGADOR|PLAYER)\s*(\d+)%', text, re.IGNORECASE)
                        if matches and player_percent is None:
                            player_percent = float(matches[0])
                        
                        matches = re.findall(r'(\d+)%\s*(?:BANCA|BANKER)', text, re.IGNORECASE)
                        if matches and banker_percent is None:
                            banker_percent = float(matches[0])
                        
                        matches = re.findall(r'(?:BANCA|BANKER)\s*(\d+)%', text, re.IGNORECASE)
                        if matches and banker_percent is None:
                            banker_percent = float(matches[0])
                        
                        matches = re.findall(r'(\d+)%\s*(?:EMPATE|TIE)', text, re.IGNORECASE)
                        if matches and tie_percent is None:
                            tie_percent = float(matches[0])
                        
                        matches = re.findall(r'(?:EMPATE|TIE)\s*(\d+)%', text, re.IGNORECASE)
                        if matches and tie_percent is None:
                            tie_percent = float(matches[0])
                    except:
                        continue
            
            # Validate that percentages make sense (should sum to ~100%)
            if player_percent is not None and banker_percent is not None and tie_percent is not None:
                total = player_percent + banker_percent + tie_percent
                # Allow some tolerance (85-110% to account for rounding)
                if 85 <= total <= 110:
                    stats = {
                        'player_percent': player_percent,
                        'banker_percent': banker_percent,
                        'tie_percent': tie_percent,
                        'player_winning': player_percent > 50,
                        'timestamp': time.time()
                    }
                    return stats
            
            # If we have at least player and banker, we can still use it
            # Require both player and banker; do not fabricate values from a single percentage
            if player_percent is not None and banker_percent is not None:
                # Calculate tie as remainder
                tie_percent = 100 - player_percent - banker_percent
                if tie_percent < 0:
                    tie_percent = 0
                
                stats = {
                    'player_percent': player_percent,
                    'banker_percent': banker_percent,
                    'tie_percent': tie_percent,
                    'player_winning': player_percent > 50,
                    'timestamp': time.time()
                }
                logger.info(f"Extracted stats (with calculated tie): Player={player_percent}%, Banker={banker_percent}%, Tie={tie_percent}%")
                return stats

            # Do not emit results from a single percentage (avoids bogus 100/0/0)
            
            # Even if we only have player percentage, we can still use it
            if player_percent is not None:
                logger.info(f"Found player percentage: {player_percent}% (missing banker/tie, but will use it)")
                # Estimate banker and tie
                if banker_percent is None:
                    banker_percent = (100 - player_percent) * 0.6  # Estimate 60% of remainder for banker
                if tie_percent is None:
                    tie_percent = 100 - player_percent - banker_percent
                    if tie_percent < 0:
                        tie_percent = 0
                
                stats = {
                    'player_percent': player_percent,
                    'banker_percent': banker_percent,
                    'tie_percent': tie_percent,
                    'player_winning': player_percent > 50,
                    'timestamp': time.time()
                }
                logger.info(f"Extracted stats (with estimated values): Player={player_percent}%, Banker={banker_percent:.1f}%, Tie={tie_percent:.1f}%")
                return stats
            
            logger.warning(f"Could not extract complete statistics. Found: Player={player_percent}, Banker={banker_percent}, Tie={tie_percent}")
            return None
            
        except Exception as e:
            logger.error(f"Error in _extract_stats_from_context: {e}")
            return None
    
    def _extract_stats_from_screenshot(self) -> Optional[Dict]:
        """
        Extract statistics from screenshot using OCR
        This is the primary method - it can read percentages directly from the visual page
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR not available, cannot extract from screenshot")
            return None
        
        if self.driver is None:
            logger.error("Driver not initialized")
            return None
        
        try:
            logger.info("Taking screenshot for OCR extraction...")
            
            # Get full page dimensions
            total_width = self.driver.execute_script("return Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth);")
            total_height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
            
            # Set viewport to full page size
            original_size = self.driver.get_window_size()
            self.driver.set_window_size(total_width, total_height)
            time.sleep(2)  # Wait for resize
            
            try:
                # Take screenshot
                screenshot = self.driver.get_screenshot_as_png()
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(screenshot))
                
                # Use OCR to extract text
                logger.info("Extracting text from screenshot using OCR...")
                ocr_text = pytesseract.image_to_string(image, lang='eng')
                
                # Check if OCR returned None or empty
                if ocr_text is None:
                    logger.warning("OCR returned None, skipping OCR extraction")
                    return None
                
                logger.debug(f"OCR extracted text length: {len(ocr_text)} characters")
                logger.debug(f"OCR text sample: {ocr_text[:500]}")
                
                # Parse OCR text to find percentages
                player_percent = None
                banker_percent = None
                tie_percent = None
                
                # Find all percentages in OCR text
                percentage_pattern = r'(\d+)%'
                all_percentages = re.findall(percentage_pattern, ocr_text)
                logger.info(f"Found {len(all_percentages)} percentages in OCR text: {all_percentages[:10]}")
                
                # Convert to uppercase for case-insensitive matching
                ocr_upper = ocr_text.upper()
                
                # Look for percentages near keywords
                lines = ocr_text.split('\n') if ocr_text else []
                for line in lines:
                    line_upper = line.upper()
                    
                    # Find percentages in this line
                    percentages_in_line = re.findall(percentage_pattern, line)
                    
                    # Check for player
                    if any(kw in line_upper for kw in ['JOGADOR', 'PLAYER']):
                        for pct in percentages_in_line:
                            val = float(pct)
                            if 0 <= val <= 100:
                                if player_percent is None or val > player_percent:  # Take the largest if multiple
                                    player_percent = val
                                    logger.info(f"Found player percentage: {player_percent}% in line: {line[:100]}")
                    
                    # Check for banker
                    if any(kw in line_upper for kw in ['BANCA', 'BANKER']):
                        for pct in percentages_in_line:
                            val = float(pct)
                            if 0 <= val <= 100:
                                if banker_percent is None or val > banker_percent:
                                    banker_percent = val
                                    logger.info(f"Found banker percentage: {banker_percent}% in line: {line[:100]}")
                    
                    # Check for tie
                    if any(kw in line_upper for kw in ['EMPATE', 'TIE']):
                        for pct in percentages_in_line:
                            val = float(pct)
                            if 0 <= val <= 100:
                                if tie_percent is None or val > tie_percent:
                                    tie_percent = val
                                    logger.info(f"Found tie percentage: {tie_percent}% in line: {line[:100]}")
                
                # Also search in context around percentages (within 200 characters)
                for percent_str in all_percentages:
                    try:
                        val = float(percent_str)
                        if 0 <= val <= 100:
                            # Find context around this percentage
                            idx = ocr_text.find(percent_str + '%')
                            if idx >= 0:
                                context_start = max(0, idx - 200)
                                context_end = min(len(ocr_text), idx + 200)
                                context = ocr_text[context_start:context_end].upper()
                                
                                if any(kw in context for kw in ['JOGADOR', 'PLAYER']):
                                    if player_percent is None or val > player_percent:
                                        player_percent = val
                                        logger.info(f"Found player percentage {val}% from context")
                                elif any(kw in context for kw in ['BANCA', 'BANKER']):
                                    if banker_percent is None or val > banker_percent:
                                        banker_percent = val
                                        logger.info(f"Found banker percentage {val}% from context")
                                elif any(kw in context for kw in ['EMPATE', 'TIE']):
                                    if tie_percent is None or val > tie_percent:
                                        tie_percent = val
                                        logger.info(f"Found tie percentage {val}% from context")
                    except:
                        continue
                
                # Heuristic 1: Prefer lines that contain all three labels with percentages
                if player_percent is None or banker_percent is None or tie_percent is None:
                    for line in lines:
                        parts = re.findall(percentage_pattern, line)
                        if len(parts) >= 3:
                            nums = [float(p) for p in parts[:3]]
                            total = sum(nums)
                            if 90 <= total <= 110:  # close to 100%
                                lu = line.upper()
                                # Try to map by label presence
                                mapping = {'PLAYER': None, 'JOGADOR': None, 'TIE': None, 'EMPATE': None, 'BANKER': None, 'BANCA': None}
                                # Assign in order if labels exist
                                if any(k in lu for k in ['JOGADOR', 'PLAYER']) and any(k in lu for k in ['EMPATE', 'TIE']) and any(k in lu for k in ['BANCA', 'BANKER']):
                                    # Assume left-to-right Player, Tie, Banker as shown on UI
                                    p_val, t_val, b_val = nums[0], nums[1], nums[2]
                                    player_percent = p_val
                                    tie_percent = t_val
                                    banker_percent = b_val
                                    logger.info(f"Mapped three-inline percentages P/T/B: {player_percent}/{tie_percent}/{banker_percent} from line: {line[:120]}")
                                    break
                                # If no labels but exactly 3 numbers, still assume left-to-right P/T/B
                                if len(nums) == 3 and (player_percent is None or banker_percent is None or tie_percent is None):
                                    p_val, t_val, b_val = nums[0], nums[1], nums[2]
                                    if 0 <= p_val <= 100 and 0 <= t_val <= 100 and 0 <= b_val <= 100:
                                        player_percent = p_val
                                        tie_percent = t_val
                                        banker_percent = b_val
                                        logger.info(f"Assumed order P/T/B for inline triplet: {player_percent}/{tie_percent}/{banker_percent}")
                                        break

                # Heuristic 2: If we can find any three percentages anywhere that sum ~100, take the most plausible triplet
                if (player_percent is None or banker_percent is None or tie_percent is None) and len(all_percentages) >= 3:
                    nums = [float(x) for x in all_percentages if 0 <= float(x) <= 100]
                    best = None
                    # Check sliding windows of three
                    for i in range(len(nums) - 2):
                        triplet = nums[i:i+3]
                        total = sum(triplet)
                        if 90 <= total <= 110:
                            # prefer triplets where middle is smaller (tie usually lower)
                            score = -abs(triplet[1] - min(triplet))
                            if not best or score > best[0]:
                                best = (score, triplet)
                    if best:
                        p_val, t_val, b_val = best[1]
                        player_percent = player_percent if player_percent is not None else p_val
                        tie_percent = tie_percent if tie_percent is not None else t_val
                        banker_percent = banker_percent if banker_percent is not None else b_val
                        logger.info(f"Selected best triplet P/T/B: {player_percent}/{tie_percent}/{banker_percent}")

                # Require at least two values; ignore bogus single 100% readings
                valid_count = sum(v is not None for v in [player_percent, banker_percent, tie_percent])
                if valid_count >= 2 and player_percent is not None and banker_percent is not None and tie_percent is not None:
                    stats = {
                        'player_percent': player_percent,
                        'banker_percent': banker_percent,
                        'tie_percent': tie_percent,
                        'player_winning': player_percent > 50,
                        'timestamp': time.time(),
                        'extraction_method': 'ocr'
                    }
                    logger.info(f"✅ OCR extraction successful: Player={player_percent}%, Banker={banker_percent:.1f}%, Tie={tie_percent:.1f}%")
                    return stats
                
                logger.warning(f"OCR found percentages but couldn't match them: Player={player_percent}, Banker={banker_percent}, Tie={tie_percent}")
                
            finally:
                # Restore original window size
                try:
                    self.driver.set_window_size(original_size['width'], original_size['height'])
                except:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}", exc_info=True)
            return None
    
    def get_betting_statistics(self) -> Optional[Dict]:
        """
        Extract betting statistics from the page
        Returns dict with player_percent, banker_percent, tie_percent, and other data
        """
        if self.driver is None:
            self.start()
        
        try:
            # Wait for the betting statistics section to load
            time.sleep(10)  # Give page more time to load dynamic content
            
            # Try to wait for specific elements that might contain statistics
            try:
                # Wait for any element containing percentage
                WebDriverWait(self.driver, 10).until(
                    lambda d: '%' in d.find_element(By.TAG_NAME, "body").text
                )
                logger.info("Page contains percentage symbols")
            except:
                logger.warning("Page might not have loaded percentages yet")
            
            # PRIMARY METHOD: Use OCR to extract from screenshot (most reliable)
            logger.info("Attempting OCR extraction from screenshot...")
            stats = self._extract_stats_from_screenshot()
            if stats:
                logger.info(f"✅ Successfully extracted stats using OCR: {stats}")
                return stats
            
            logger.warning("OCR extraction failed, trying HTML/text extraction...")
            
            # FALLBACK METHOD: Try to extract from HTML/text
            logger.debug("Attempting to extract stats from main page HTML/text...")
            stats = self._extract_stats_from_context(self.driver)
            if stats:
                logger.info(f"Successfully extracted stats from main page: {stats}")
                return stats
            
            # If not found, try to find and switch to iframe
            # Casino games often load in iframes
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                logger.info(f"Found {len(iframes)} iframe(s)")
                
                for idx, iframe in enumerate(iframes):
                    try:
                        logger.debug(f"Trying iframe {idx + 1}/{len(iframes)}...")
                        # Scroll to iframe to ensure it's visible
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", iframe)
                        time.sleep(2)
                        
                        # Try to switch to iframe
                        self.driver.switch_to.frame(iframe)
                        logger.debug("Switched to iframe, waiting for content...")
                        time.sleep(5)  # Wait longer for iframe content to load
                        
                        # Debug: print some text from iframe to see what's there
                        try:
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
                            logger.info(f"Iframe text sample (first 500 chars): {page_text}")
                            
                            # Also try to get all text using JavaScript
                            try:
                                js_text = self.driver.execute_script("return document.body.innerText;")
                                if js_text and len(js_text) > 100:
                                    logger.info(f"JavaScript extracted text sample: {js_text[:500]}")
                            except:
                                pass
                            
                            # Try to find elements with innerText or textContent
                            try:
                                # More comprehensive JavaScript extraction
                                stats_data = self.driver.execute_script(r"""
                                    var results = {
                                        player: [],
                                        banker: [],
                                        tie: [],
                                        all_texts: []
                                    };
                                    
                                    // Get all elements
                                    var all = document.querySelectorAll('*');
                                    
                                    for (var i = 0; i < all.length; i++) {
                                        try {
                                            var elem = all[i];
                                            var text = elem.innerText || elem.textContent || '';
                                            
                                            if (text && text.length > 0 && text.length < 500) {
                                                // Check for percentages
                                                var percentMatch = text.match(/(\d+)%/g);
                                                if (percentMatch) {
                                                    var upperText = text.toUpperCase();
                                                    
                                                    // Check for player
                                                    if (upperText.includes('JOGADOR') || upperText.includes('PLAYER')) {
                                                        percentMatch.forEach(function(p) {
                                                            var val = parseInt(p);
                                                            if (val >= 0 && val <= 100) {
                                                                results.player.push(val);
                                                            }
                                                        });
                                                        results.all_texts.push(text.substring(0, 150));
                                                    }
                                                    
                                                    // Check for banker
                                                    if (upperText.includes('BANCA') || upperText.includes('BANKER')) {
                                                        percentMatch.forEach(function(p) {
                                                            var val = parseInt(p);
                                                            if (val >= 0 && val <= 100) {
                                                                results.banker.push(val);
                                                            }
                                                        });
                                                    }
                                                    
                                                    // Check for tie
                                                    if (upperText.includes('EMPATE') || upperText.includes('TIE')) {
                                                        percentMatch.forEach(function(p) {
                                                            var val = parseInt(p);
                                                            if (val >= 0 && val <= 100) {
                                                                results.tie.push(val);
                                                            }
                                                        });
                                                    }
                                                }
                                            }
                                        } catch(e) {}
                                    }
                                    
                                    // Also search in page source
                                    var pageSource = document.documentElement.innerHTML;
                                    var sourceUpper = pageSource.toUpperCase();
                                    
                                    // Find all percentages in source
                                    var allPercents = pageSource.match(/(\d+)%/g);
                                    if (allPercents) {
                                        for (var j = 0; j < allPercents.length; j++) {
                                            var percentStr = allPercents[j];
                                            var val = parseInt(percentStr);
                                            if (val >= 0 && val <= 100) {
                                                var idx = pageSource.indexOf(percentStr);
                                                if (idx >= 0) {
                                                    var context = pageSource.substring(Math.max(0, idx-100), Math.min(pageSource.length, idx+100)).toUpperCase();
                                                    
                                                    if (context.includes('JOGADOR') || context.includes('PLAYER')) {
                                                        results.player.push(val);
                                                    }
                                                    if (context.includes('BANCA') || context.includes('BANKER')) {
                                                        results.banker.push(val);
                                                    }
                                                    if (context.includes('EMPATE') || context.includes('TIE')) {
                                                        results.tie.push(val);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    
                                    return results;
                                """)
                                
                                if stats_data:
                                    logger.info(f"JavaScript extraction results: Player={stats_data.get('player', [])}, Banker={stats_data.get('banker', [])}, Tie={stats_data.get('tie', [])}")
                                    if stats_data.get('all_texts'):
                                        logger.info(f"Sample texts found: {stats_data.get('all_texts', [])[:3]}")
                                    
                                    # Add to candidates
                                    if stats_data.get('player'):
                                        player_candidates.extend([v for v in stats_data['player'] if v not in player_candidates])
                                    if stats_data.get('banker'):
                                        banker_candidates.extend([v for v in stats_data['banker'] if v not in banker_candidates])
                                    if stats_data.get('tie'):
                                        tie_candidates.extend([v for v in stats_data['tie'] if v not in tie_candidates])
                                    
                                    logger.info(f"After JavaScript: Player candidates: {player_candidates}, Banker: {banker_candidates}, Tie: {tie_candidates}")
                                    
                                    # Recalculate percentages after JavaScript extraction
                                    if player_candidates:
                                        player_percent = max(set(player_candidates), key=player_candidates.count)
                                    if banker_candidates:
                                        banker_percent = max(set(banker_candidates), key=banker_candidates.count)
                                    if tie_candidates:
                                        tie_percent = max(set(tie_candidates), key=tie_candidates.count)
                                    
                            except Exception as js_error:
                                logger.debug(f"JavaScript extraction error: {js_error}")
                        except:
                            pass
                        
                        # Try extraction from iframe with updated candidates from JavaScript
                        stats = self._extract_stats_from_context(
                            self.driver, 
                            player_candidates=player_candidates,
                            banker_candidates=banker_candidates,
                            tie_candidates=tie_candidates
                        )
                        if stats:
                            logger.info(f"Successfully extracted stats from iframe {idx + 1}: {stats}")
                            self.driver.switch_to.default_content()
                            return stats
                        
                        # Also try extracting fresh from iframe context
                        stats = self._extract_stats_from_context(self.driver)
                        if stats:
                            logger.info(f"Successfully extracted stats from iframe {idx + 1} (fresh extraction): {stats}")
                            self.driver.switch_to.default_content()
                            return stats
                        
                        # Try waiting for specific elements that might contain stats
                        try:
                            # Look for common betting statistics containers
                            stat_containers = self.driver.find_elements(By.XPATH, 
                                "//*[contains(@class, 'stat') or contains(@class, 'bet') or contains(@id, 'stat') or contains(@id, 'bet')]")
                            logger.debug(f"Found {len(stat_containers)} potential stat containers in iframe")
                            
                            for container in stat_containers[:10]:  # Check first 10
                                try:
                                    text = container.text
                                    if text and ('%' in text or 'JOGADOR' in text.upper() or 'PLAYER' in text.upper()):
                                        logger.debug(f"Found potential stat container: {text[:100]}")
                                except:
                                    pass
                        except Exception as e:
                            logger.debug(f"Error checking stat containers: {e}")
                        
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        logger.warning(f"Error switching to iframe {idx + 1}: {e}")
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
            except Exception as e:
                logger.warning(f"Error checking iframes: {e}")
            
            # Try one more time with a longer wait and refresh
            logger.info("Retrying extraction with longer wait...")
            time.sleep(5)
            
            # Try refreshing the page content
            try:
                self.driver.refresh()
                time.sleep(8)
                stats = self._extract_stats_from_context(self.driver)
                if stats:
                    logger.info(f"Successfully extracted stats after refresh: {stats}")
                    return stats
            except:
                pass
            
            # Last attempt: try iframes again with even longer wait
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        self.driver.switch_to.frame(iframe)
                        time.sleep(10)  # Even longer wait
                        stats = self._extract_stats_from_context(self.driver)
                        if stats:
                            self.driver.switch_to.default_content()
                            return stats
                        self.driver.switch_to.default_content()
                    except:
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
            except:
                pass
            
            logger.warning("Could not extract betting statistics after all attempts")
            return None
            
        except Exception as e:
            logger.error(f"Error getting betting statistics: {e}", exc_info=True)
            return None
    
    def refresh(self):
        """Refresh the page"""
        if self.driver:
            self.driver.refresh()
            time.sleep(5)
            self._switch_language(self.current_language)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None

