import csv
import os
import re
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CURATED_ARTISTS_FILE = "data/curated_artists.csv"
# We will now look for the follow button and navigate up to the user cell.
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
            # Skip header
            next(reader, None)
            return {row[1] for row in reader}
        except (StopIteration, IndexError):
            return set()


async def curate_artist(driver, artist_url):
    """
    Scrapes the followed list of a given artist and saves the data.
    """
    print(f"Curating artist: {artist_url}")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(CURATED_ARTISTS_FILE), exist_ok=True)

    # Navigate to the 'following' page
    following_url = f"{artist_url.replace('x.com', 'twitter.com')}/following"
    print(f"Navigating to {following_url}")
    driver.get(following_url)

    # Wait for the page to load
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, USER_ROW_SELECTOR))
        )
    except Exception:
        print("Could not find user list on the page. The user may have a private profile or the page structure has changed.")
        # Even if we can't find followers, we can still try to add the main artist
        pass

    existing_handles = get_curated_artists()
    print(f"Found {len(existing_handles)} existing curated artists.")
    
    new_artists = []

    # Add the artist being curated if they don't exist
    try:
        artist_handle_match = re.search(r'(?:twitter|x)\.com/([^/]+)', artist_url)
        if artist_handle_match:
            artist_handle = f"@{artist_handle_match.group(1)}"
            if artist_handle not in existing_handles:
                # Wait for the username to be present on the profile page
                user_name_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[role="heading"] span'))
                )
                user_name = user_name_element.text
                
                print(f"Adding the artist being curated: {user_name} ({artist_handle})")
                new_artists.append((user_name, artist_handle, artist_url, datetime.now().isoformat()))
                # Add to existing_handles to prevent duplication if they are in their own following list
                existing_handles.add(artist_handle)
    except Exception as e:
        print(f"Could not add the main artist '{artist_url}'. Reason: {e}")

    last_height = driver.execute_script("return document.body.scrollHeight")
    
    processed_users = set()

    while True:
        # Find the follow buttons, then navigate up to the user cell
        button_elements = driver.find_elements(By.CSS_SELECTOR, USER_ROW_SELECTOR)
        
        for button_element in button_elements:
            try:
                user_element = button_element.find_element(By.XPATH, "./../..")

                # Find profile links, skip if none are found
                profile_links = user_element.find_elements(By.CSS_SELECTOR, 'a[role="link"]')
                if not profile_links:
                    continue
                
                first_link = profile_links[0]
                user_path = first_link.get_attribute('href')
                
                # Check if we have already processed this user in this run
                if not user_path or user_path in processed_users:
                    continue

                if not (user_path.startswith('https://twitter.com/') or user_path.startswith('https://x.com/')):
                    continue
                
                processed_users.add(user_path)
                
                user_url = user_path
                user_path_slug = user_url.replace('https://twitter.com', '').replace('https://x.com', '')

                # Find name and handle links using the path and tabindex
                name_element_link = user_element.find_element(By.CSS_SELECTOR, f'a[href="{user_path_slug}"]:not([tabindex="-1"])')
                handle_element_link = user_element.find_element(By.CSS_SELECTOR, f'a[href="{user_path_slug}"][tabindex="-1"]')
                
                # Extract text
                user_name = name_element_link.find_element(By.CSS_SELECTOR, 'span > span').text
                user_handle = handle_element_link.find_element(By.CSS_SELECTOR, 'span').text

                if user_handle and user_handle not in existing_handles and user_handle not in [a[1] for a in new_artists]:
                    print(f"Found new artist: {user_name} ({user_handle})")
                    new_artists.append((user_name, user_handle, user_url, datetime.now().isoformat()))

            except Exception as e:
                # This may happen if the element structure is unexpected.
                # print(f"Skipping an element due to error: {e}")
                pass

        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new content to load
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Reached the end of the list
            break
        last_height = new_height

    if not new_artists:
        print("No new artists found to add.")
        return

    print(f"Found {len(new_artists)} new artists to add.")

    # Append to CSV
    file_exists = os.path.exists(CURATED_ARTISTS_FILE)
    with open(CURATED_ARTISTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(CURATED_ARTISTS_FILE) == 0:
            writer.writerow(["username", "handle", "url", "timestamp"])
        
        writer.writerows(new_artists)
    
    print(f"Successfully added {len(new_artists)} new artists to {CURATED_ARTISTS_FILE}")
