# Plan: Scrape X "For You" Timeline

Goal: Use a logged-in browser session to scroll the **For You** tab and save tweets’ media + stats.

## Stack

- Python 3
- Selenium for browser automation
- `aiohttp` for concurrent media downloads
- `python-dotenv` for config
- Output: JSONL + media files

## Proposed Structure

- `main.py`: Entry point, CLI parsing, orchestration.
- `scraper.py`: Selenium logic for auth, scrolling, and data extraction.
- `downloader.py`: `aiohttp`-based concurrent media downloading.
- `config.py`: Loads credentials and settings from `.env`.

## Core Steps

1. **Auth & Session**
   - Load `X_USER` / `X_PASS` from a `.env` file.
   - Log in and save session cookies to a file for reuse.

2. **Scrolling & Extraction**
   - Open **For You** tab (`https://x.com/home`).
   - Loop: scroll, wait, collect new tweets. Stop on time/tweet limit or no new content.
   - Robustly extract data (ID, author, text, stats, media URLs), handling missing elements gracefully.

3. **Download & Save**
   - Use `downloader.py` to concurrently download all media from a batch of tweets.
   - Implement retry logic for failed downloads.
   - Append per-tweet JSON record to a `.jsonl` file.
   - Save all collected data on graceful shutdown (e.g., Ctrl+C).

4. **Config & CLI**
   - Script options: `--max-tweets`, `--max-minutes`, `--output-dir`, `--headless`.
   - The entry script will orchestrate the flow: load config → scroll & extract → download → save.
