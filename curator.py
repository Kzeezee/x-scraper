import csv
import os
import re
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CURATED_ARTISTS_FILE = "data/curated_artists.csv"
USER_ROW_SELECTOR = '[data-testid$="-follow"]'

def get_curated_artists():
    """
    Reads the curated artists from the CSV file and returns a set of user handles.
    """
    if not os.path.exists(CURATED_ARTISTS_FILE):
        return set()

    with open(CURATED_ARTISTS_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            next(reader, None)  # Skip header
            return {row[1] for row in reader}
        except (StopIteration, IndexError):
            return set()

async def curate_recursively(driver, artist_url, depth, visited_urls=None):
    """
    Recursively scrapes the followed list of artists.
    """
    if visited_urls is None:
        visited_urls = set()

    if depth < 0 or artist_url in visited_urls:
        return

    visited_urls.add(artist_url)

    print(f"Curating artist: {artist_url} at depth {depth}")
    scanned_artists = await _curate_single_artist(driver, artist_url)

    if depth > 0:
        for _, _, next_artist_url, _ in scanned_artists:
            await curate_recursively(driver, next_artist_url, depth - 1, visited_urls)

async def _curate_single_artist(driver, artist_url):
    """
    Scrapes the followed list of a given artist, saves new artists to the CSV,
    and returns a list of all scanned artists on the page.
    """
    os.makedirs(os.path.dirname(CURATED_ARTISTS_FILE), exist_ok=True)

    following_url = f"{artist_url.replace('x.com', 'twitter.com')}/following"
    print(f"Navigating to {following_url}")
    driver.get(following_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, USER_ROW_SELECTOR))
        )
    except Exception:
        print("Could not find user list on the page.")
        return []

    existing_handles = get_curated_artists()
    print(f"Found {len(existing_handles)} existing curated artists.")
    
    new_artists_to_write = []
    scanned_artists_on_page = []

    # Add the artist being curated if they are new
    try:
        artist_handle_match = re.search(r'(?:twitter|x)\.com/([^/]+)', artist_url)
        if artist_handle_match:
            artist_handle = f"@{artist_handle_match.group(1)}"
            if artist_handle not in existing_handles:
                handle_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//span[text()='{artist_handle}']"))
                )
                user_name_element = handle_element.find_element(By.XPATH, "./../preceding-sibling::h2/span")
                user_name = user_name_element.text
                
                print(f"Adding the artist being curated: {user_name} ({artist_handle})")
                artist_data = (user_name, artist_handle, artist_url, datetime.now().isoformat())
                new_artists_to_write.append(artist_data)
                existing_handles.add(artist_handle)
    except Exception as e:
        print(f"Could not add the main artist '{artist_url}'. Reason: {e}")

    last_height = driver.execute_script("return document.body.scrollHeight")
    processed_users_in_run = set()

    while True:
        button_elements = driver.find_elements(By.CSS_SELECTOR, USER_ROW_SELECTOR)
        
        for button_element in button_elements:
            try:
                user_element = button_element.find_element(By.XPATH, "./../..")
                profile_links = user_element.find_elements(By.CSS_SELECTOR, 'a[role="link"]')
                if not profile_links:
                    continue
                
                user_path = profile_links[0].get_attribute('href')
                if not user_path or user_path in processed_users_in_run:
                    continue

                if not (user_path.startswith('https://twitter.com/') or user_path.startswith('https://x.com/')):
                    continue
                
                processed_users_in_run.add(user_path)
                
                user_url = user_path
                user_path_slug = user_url.replace('https://twitter.com', '').replace('https://x.com', '')

                name_element_link = user_element.find_element(By.CSS_SELECTOR, f'a[href="{user_path_slug}"]:not([tabindex="-1"])')
                handle_element_link = user_element.find_element(By.CSS_SELECTOR, f'a[href="{user_path_slug}"][tabindex="-1"]')
                
                user_name = name_element_link.find_element(By.CSS_SELECTOR, 'span > span').text
                user_handle = handle_element_link.find_element(By.CSS_SELECTOR, 'span').text

                artist_data = (user_name, user_handle, user_url, datetime.now().isoformat())
                scanned_artists_on_page.append(artist_data)

                if user_handle and user_handle not in existing_handles:
                    print(f"Found new artist: {user_name} ({user_handle})")
                    new_artists_to_write.append(artist_data)
                    existing_handles.add(user_handle)

            except Exception:
                pass

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    if new_artists_to_write:
        print(f"Found {len(new_artists_to_write)} new artists to add.")
        file_exists = os.path.exists(CURATED_ARTISTS_FILE)
        with open(CURATED_ARTISTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(CURATED_ARTISTS_FILE) == 0:
                writer.writerow(["username", "handle", "url", "timestamp"])
            writer.writerows(new_artists_to_write)
        print(f"Successfully added {len(new_artists_to_write)} new artists to {CURATED_ARTISTS_FILE}")
    else:
        print("No new artists found to add.")

    return scanned_artists_on_page