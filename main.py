import argparse
import asyncio
import json
import os
import traceback
import datetime
from scraper import XScraper
from downloader import download_media
from curator import curate_recursively

async def run_scraper(args):
    """Runs the X/Twitter timeline scraper."""
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

            download_map = {url: path for url, path in downloaded_media_paths}
            
            with open(jsonl_output_path, "a", encoding="utf-8") as f:
                for tweet in collected_tweets:
                    local_media_paths = []
                    for original_url in tweet["media_urls"]:
                        local_media_paths.append(download_map.get(original_url, original_url))
                    tweet["media_local_paths"] = local_media_paths
                    f.write(json.dumps(tweet, ensure_ascii=False) + "\n")
            
            print(f"Scraping complete. Data saved to {jsonl_output_path}")
            print(f"Downloaded media to {media_output_path}")

        else:
            print("Login failed. Exiting.")
    finally:
        if scraper:
            scraper.close()

async def run_curator(args):
    """Runs the artist curator."""
    scraper = None
    try:
        scraper = XScraper(headless=args.headless)
        if scraper.login():
            print("Login successful. Starting curation...")
            await curate_recursively(scraper.driver, args.artist_url, args.depth)
        else:
            print("Login failed. Exiting.")
    finally:
        if scraper:
            scraper.close()

async def main():
    parser = argparse.ArgumentParser(description="Scrape X (Twitter).")
    parser.add_argument("--headless", action="store_true",
                        help="Run the browser in headless mode (without a UI).")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scraper command
    parser_scrape = subparsers.add_parser("scrape", help="Scrape the 'For You' timeline.")
    parser_scrape.add_argument("--max-tweets", type=int, default=50,
                               help="Maximum number of tweets to scrape.")
    parser_scrape.add_argument("--max-minutes", type=int, default=5,
                               help="Maximum number of minutes to run the scraper.")
    parser_scrape.add_argument("--output-dir", type=str, default="data",
                               help="Base directory to save scraped data and media.")

    # Curator command
    parser_curate = subparsers.add_parser("curate", help="Curate artists by scraping their followed list.")
    parser_curate.add_argument("artist_url", type=str, help="The URL of the artist's profile to curate.")
    parser_curate.add_argument("--depth", type=int, default=1, help="The recursion depth for curating artists.")

    args = parser.parse_args()

    try:
        if args.command == "scrape":
            await run_scraper(args)
        elif args.command == "curate":
            await run_curator(args)
    except Exception:
        print(f"An error occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())