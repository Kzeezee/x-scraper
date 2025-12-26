import os
import time
import json
import datetime
import re # For extracting tweet IDs and media URLs

import undetected_chromedriver as uc # Import undetected_chromedriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import config # Assuming config.py is in the same directory

# CSS selectors for various tweet elements
TWEET_SELECTORS = {
    "tweet_container": 'article[data-testid="tweet"]',
    "tweet_id_url": 'a[href*="/status/"]',
    "author_link": 'div[data-testid="User-Name"] a',
    "timestamp_link": 'a > time',
    "text": 'div[data-testid="tweetText"]',
    "media_img": 'div[data-testid="tweetPhoto"] img',
    "media_video": 'div[data-testid="videoPlayer"] video',
    "stats_group": 'div[role="group"]', # As per user request
}

STAT_PATTERNS = {
    "reply": r"([\d,]+)\s*(?:件の返信|repl(?:y|ies))",
    "repost": r"([\d,]+)\s*(?:件のリポスト|repost(?:s)?)",
    "like": r"([\d,]+)\s*(?:件のいいね|like(?:s)?)",
    "bookmark": r"([\d,]+)\s*(?:件のブックマーク|bookmark(?:s)?)",
    "view": r"([\d,]+)\s*(?:件の表示|view(?:s)?)",
}

class XScraper:
    def __init__(self, headless=True, cookie_file="cookies.json"):
        self.cookie_file = cookie_file
        self.driver = self._initialize_driver(headless)
        self.wait = WebDriverWait(self.driver, 120) # Increased timeout for manual login

    def _initialize_driver(self, headless):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new") # Use new headless mode
        
        chrome_options.binary_location = "/usr/bin/google-chrome-beta"

        driver = uc.Chrome(options=chrome_options, headless=headless)
        
        return driver

    def _save_cookies(self):
        with open(self.cookie_file, 'w') as f:
            json.dump(self.driver.get_cookies(), f)

    def _load_cookies(self):
        if os.path.exists(self.cookie_file):
            print(f"Cookie file found at '{self.cookie_file}'.")
            try:
                with open(self.cookie_file, 'r') as f:
                    cookies = json.load(f)
                
                print(f"Loaded {len(cookies)} cookies from file.")
                for i, cookie in enumerate(cookies):
                    if "name" not in cookie or "value" not in cookie:
                        continue
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    if 'domain' in cookie and cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain'][1:]
                    
                    self.driver.add_cookie(cookie)
                
                print("Successfully added cookies to the browser session.")
                return True
            except Exception as e:
                print(f"An error occurred while processing cookies: {e}")
                return False
        
        print(f"Cookie file not found at '{self.cookie_file}'.")
        return False

    def login(self):
        print("Attempting to load cookies...")
        self.driver.get("https://x.com") 

        if self._load_cookies():
            print("Cookies loaded, refreshing page to apply session...")
            self.driver.get("https://x.com/home")
            time.sleep(config.LOGIN_COOKIE_APPLY_DELAY)
            
            print(f"Current URL after loading cookies: {self.driver.current_url}")
            if "home" in self.driver.current_url:
                print("Cookies appear to be valid. Logged in successfully.")
                return True
            else:
                print("Cookies did not result in a logged-in session.")
        
        print("Proceeding with manual login flow...")
        self.driver.get("https://x.com/i/flow/login")

        try:
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "text")))
            username_input.send_keys(config.X_USER)
            
            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']/ancestor::button")))
            next_button.click()

            time.sleep(config.LOGIN_FORM_TRANSITION_DELAY)

            if "Phone, email, or username" in self.driver.page_source:
                 print("Additional verification might be required. Please check browser.")
                 pass

            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(config.X_PASS)
            
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']/ancestor::button")))
            login_button.click()

            self.wait.until(EC.url_contains("home"))
            print("Successfully logged in.")
            self._save_cookies()
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def _scroll_and_extract_tweets(self, max_tweets=None, max_minutes=None):
        seen_tweet_ids = set()
        collected_tweets_data = []
        start_time = time.time()
        
        max_tweets = max_tweets if max_tweets is not None else float('inf')
        max_minutes = max_minutes if max_minutes is not None else float('inf')

        print(f"Starting to scroll and extract tweets (Max tweets: {max_tweets if max_tweets != float('inf') else 'unlimited'}, Max minutes: {max_minutes if max_minutes != float('inf') else 'unlimited'})...")

        last_tweet_count = 0
        consecutive_stalls = 0
        
        while len(collected_tweets_data) < max_tweets and (time.time() - start_time) < (max_minutes * 60):
            # Check for rate limit message
            try:
                rate_limit_element = self.driver.find_element(By.XPATH, "//span[contains(text(), '問題が発生しました。再読み込みしてください。')]")
                if rate_limit_element:
                    print(f"Rate limit detected. Waiting for {config.RATE_LIMIT_DELAY} seconds...")
                    time.sleep(config.RATE_LIMIT_DELAY)
                    print("Resuming after rate limit...")
                    self.driver.refresh()
                    time.sleep(config.SEARCH_PAGE_LOAD_DELAY) # Wait for page to load after refresh
                    continue
            except:
                pass # No rate limit element found

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(config.SCROLL_NEW_CONTENT_DELAY)
            
            tweets_on_page = self.driver.find_elements(By.CSS_SELECTOR, TWEET_SELECTORS["tweet_container"])
            
            if not tweets_on_page:
                print("No tweets found on page, stopping.")
                break

            for tweet_element in tweets_on_page:
                if len(collected_tweets_data) >= max_tweets:
                    break
                try:
                    tweet_url_element = tweet_element.find_element(By.CSS_SELECTOR, TWEET_SELECTORS["tweet_id_url"])
                    tweet_url = tweet_url_element.get_attribute("href")
                    
                    match = re.search(r'/status/(\d+)', tweet_url)
                    if not match: continue
                    tweet_id = match.group(1)

                    if tweet_id in seen_tweet_ids: continue
                    seen_tweet_ids.add(tweet_id)
                    
                    tweet_data = {
                        "id": tweet_id, "url": tweet_url, "author": None, "timestamp": None,
                        "text": None, "stats": {}, "media_urls": [],
                    }

                    try: tweet_data["author"] = tweet_element.find_element(By.CSS_SELECTOR, TWEET_SELECTORS["author_link"]).text
                    except: pass
                    try: tweet_data["timestamp"] = tweet_element.find_element(by=By.CSS_SELECTOR, value=TWEET_SELECTORS["timestamp_link"]).get_attribute("datetime")
                    except: pass
                    try: tweet_data["text"] = tweet_element.find_element(By.CSS_SELECTOR, TWEET_SELECTORS["text"]).text
                    except: pass

                    try:
                        stats_group = tweet_element.find_element(By.CSS_SELECTOR, TWEET_SELECTORS["stats_group"])
                        aria_label = stats_group.get_attribute('aria-label')
                        if aria_label:
                            for stat_name, pattern in STAT_PATTERNS.items():
                                match_stat = re.search(pattern, aria_label)
                                if match_stat:
                                    tweet_data["stats"][stat_name] = int(match_stat.group(1).replace(',', ''))
                    except Exception: pass

                    try:
                        media_elements = tweet_element.find_elements(By.CSS_SELECTOR, f'{TWEET_SELECTORS["media_img"]}, {TWEET_SELECTORS["media_video"]}')
                        for media_el in media_elements:
                            src = media_el.get_attribute("src")
                            if src and not src.startswith("data:"):
                                tweet_data["media_urls"].append(src)
                    except Exception: pass

                    collected_tweets_data.append(tweet_data)
                    print(f"Collected tweet {len(collected_tweets_data)}: {tweet_id}")

                except Exception as e:
                    print(f"Error processing a tweet: {e}")
                    continue
            
            if len(collected_tweets_data) == last_tweet_count:
                consecutive_stalls += 1
                if consecutive_stalls >= config.SCROLL_MAX_STALLS:
                    print("No new tweets found after multiple scrolls, stopping.")
                    break
            else:
                consecutive_stalls = 0

            last_tweet_count = len(collected_tweets_data)

        print(f"Finished scrolling. Total tweets collected: {len(collected_tweets_data)}")
        return collected_tweets_data

    def scroll_and_extract(self, max_tweets=50, max_minutes=5):
        if "home" not in self.driver.current_url:
            print("Navigating to X home page (For You tab)...")
            self.driver.get("https://x.com/home")
            self.wait.until(EC.url_contains("home"))
            time.sleep(config.SCROLL_INITIAL_LOAD_DELAY)
        
        return self._scroll_and_extract_tweets(max_tweets=max_tweets, max_minutes=max_minutes)

    def scrape_from_search(self, search_url, limit=None):
        print(f"Navigating to search URL: {search_url}")
        self.driver.get(search_url)
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TWEET_SELECTORS["tweet_container"])))
        except:
            print("No tweets found for the given search criteria.")
            return []
        time.sleep(config.SEARCH_PAGE_LOAD_DELAY)
        
        return self._scroll_and_extract_tweets(max_tweets=limit)


    def close(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    scraper = None
    try:
        scraper = XScraper(headless=False)
        if scraper.login():
            scraper.scroll_and_extract(max_tweets=20)
        else:
            print("Could not log in. Exiting.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if scraper:
            scraper.close()