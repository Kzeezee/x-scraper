import argparse
import asyncio
import json
import os
import traceback # Import traceback for detailed error logging
import datetime # Import datetime for timestamping output directories
from scraper import XScraper
from downloader import download_media

async def main():
    parser = argparse.ArgumentParser(description="Scrape X (Twitter) 'For You' timeline.")
    parser.add_argument("--max-tweets", type=int, default=50,
                        help="Maximum number of tweets to scrape.")
    parser.add_argument("--max-minutes", type=int, default=5,
                        help="Maximum number of minutes to run the scraper.")
    parser.add_argument("--output-dir", type=str, default="output",
                        help="Base directory to save scraped data and media.")
    parser.add_argument("--headless", action="store_true",
                        help="Run the browser in headless mode (without a UI).")
    
    args = parser.parse_args()

    # Create a timestamped subdirectory within the specified output_dir
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(args.output_dir, timestamp)

    if not os.path.exists(run_output_dir):
        os.makedirs(run_output_dir)
    
    jsonl_output_path = os.path.join(run_output_dir, "tweets.jsonl")
    media_output_path = os.path.join(run_output_dir, "media")

    scraper = None
    try:
        scraper = XScraper(headless=args.headless)
        if scraper.login():
            print("Login successful. Starting to scrape...")
            collected_tweets = scraper.scroll_and_extract(
                max_tweets=args.max_tweets,
                max_minutes=args.max_minutes
            )

            print(f"Scraped {len(collected_tweets)} tweets. Starting media download...")
            
            all_media_urls = []
            for tweet in collected_tweets:
                all_media_urls.extend(tweet["media_urls"])

            downloaded_media_paths = await download_media(all_media_urls, media_output_path)

            # Map downloaded paths back to tweets
            download_map = {url: path for url, path in downloaded_media_paths}
            
            with open(jsonl_output_path, "a", encoding="utf-8") as f:
                for tweet in collected_tweets:
                    # Replace original media URLs with local paths if downloaded
                    local_media_paths = []
                    for original_url in tweet["media_urls"]:
                        local_media_paths.append(download_map.get(original_url, original_url))
                    tweet["media_local_paths"] = local_media_paths
                    f.write(json.dumps(tweet, ensure_ascii=False) + "\n")
            
            print(f"Scraping complete. Data saved to {jsonl_output_path}")
            print(f"Downloaded media to {media_output_path}")

        else:
            print("Login failed. Exiting.")
    except Exception:
        print(f"An error occurred during the scraping process:")
        traceback.print_exc() # Print the full traceback
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    asyncio.run(main())