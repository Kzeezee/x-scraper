import argparse
import asyncio
import json
import os
import traceback
import datetime
from urllib.parse import quote
from scraper import XScraper
from downloader import download_media
from curator import curate_recursively
from selector import run_selector

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
            
            with open(jsonl_output_path, "w", encoding="utf-8") as f:
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

async def run_user_scraper(args):
    """Runs the user-specific media scraper."""
    # Build the search query
    query_parts = [
        f"from:{args.username}",
        "filter:media",
        "-filter:retweets"
    ]
    if args.min_likes > 0:
        query_parts.append(f"min_faves:{args.min_likes}")
    if args.since:
        query_parts.append(f"since:{args.since}")
    if args.until:
        query_parts.append(f"until:{args.until}")
    
    search_query = " ".join(query_parts)
    
    # URL encode the query
    encoded_query = quote(search_query)
    
    search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"
    
    print(f"Constructed search URL: {search_url}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(args.output_dir, f"{args.username}_{timestamp}")

    if not os.path.exists(run_output_dir):
        os.makedirs(run_output_dir)
    
    jsonl_output_path = os.path.join(run_output_dir, "tweets.jsonl")
    media_output_path = os.path.join(run_output_dir, "media")

    scraper = None
    try:
        scraper = XScraper(headless=args.headless)
        if scraper.login():
            print("Login successful. Starting to scrape...")
            collected_tweets = scraper.scrape_from_search(
                search_url=search_url,
                limit=args.limit
            )

            print(f"Scraped {len(collected_tweets)} tweets. Starting media download...")
            
            all_media_urls = []
            for tweet in collected_tweets:
                all_media_urls.extend(tweet["media_urls"])

            downloaded_media_paths = await download_media(all_media_urls, media_output_path)

            download_map = {url: path for url, path in downloaded_media_paths}
            
            with open(jsonl_output_path, "w", encoding="utf-8") as f:
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

    # Selector command
    parser_select = subparsers.add_parser("select", help="Select and filter tweets from a directory.")
    parser_select.add_argument("--input-dir", type=str, required=True,
                               help="Path to the directory containing tweets.jsonl and media folder.")
    parser_select.add_argument("--output-dir", type=str, required=True,
                               help="Path to the directory where the selected data will be saved.")
    parser_select.add_argument("--min-replies", type=int, default=0,
                               help="Minimum number of replies.")
    parser_select.add_argument("--min-reposts", type=int, default=0,
                               help="Minimum number of reposts.")
    parser_select.add_argument("--min-likes", type=int, default=0,
                               help="Minimum number of likes.")
    parser_select.add_argument("--min-bookmarks", type=int, default=0,
                               help="Minimum number of bookmarks.")
    parser_select.add_argument("--min-views", type=int, default=0,
                               help="Minimum number of views.")
    parser_select.add_argument("--sort-by", type=str, default="views", choices=["likes", "views"],
                               help="How to sort the output tweets.jsonl. Options: likes, views.")
    parser_select.add_argument("--action", type=str, default="copy", choices=["copy", "move"],
                               help="Whether to copy or move media files. Options: copy, move.")

    # User Scraper command
    parser_user_scrape = subparsers.add_parser("user_scrape", help="Scrape media tweets from a specific user.")
    parser_user_scrape.add_argument("--username", type=str, required=True,
                                    help="The X username of the target user.")
    parser_user_scrape.add_argument("--limit", type=int, default=None,
                                    help="Maximum number of recent tweets to scrape.")
    parser_user_scrape.add_argument("--min-likes", type=int, default=0,
                                    help="Minimum number of likes for a tweet to be scraped.")
    parser_user_scrape.add_argument("--since", type=str, default=None,
                                    help="Start date for scraping (YYYY-MM-DD).")
    parser_user_scrape.add_argument("--until", type=str, default=None,
                                    help="End date for scraping (YYYY-MM-DD).")
    parser_user_scrape.add_argument("--output-dir", type=str, default="data",
                               help="Base directory to save scraped data and media.")

    args = parser.parse_args()

    try:
        if args.command == "scrape":
            await run_scraper(args)
        elif args.command == "curate":
            await run_curator(args)
        elif args.command == "select":
            await run_selector(args)
        elif args.command == "user_scrape":
            await run_user_scraper(args)
    except Exception:
        print(f"An error occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())