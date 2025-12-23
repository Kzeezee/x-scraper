# X Scraper - Development Plan

## 1. Main Script CLI

The `main.py` script will be updated to provide a command-line interface (CLI) with the following functions:

*   **`scrape`**: This command will execute the existing functionality of scraping the "For You" timeline.
*   **`curate`**: This command will be used for artist curation. It will take a Twitter profile URL as an argument.

## 2. Artist Curation Functionality

A new module will be created to handle the artist curation process.

### Inputs

*   A Twitter user's profile URL.

### Process

1.  Navigate to the "Following" page of the provided Twitter user.
2.  Iterate through the list of followed accounts.
3.  For each account, extract the following metadata:
    *   Username
    *   User Handle (e.g., @username)
    *   User Profile URL
    *   Timestamp of when the data was captured.
4.  Store the captured data in a persistent format (e.g., a CSV file).
5.  Before storing, check for duplicates to ensure that each unique user is only recorded once.

## 3. Data Storage

*   A `data` directory will be used to store the outputs.
*   The curated artist data will be stored in a CSV file named `curated_artists.csv`.
*   The scraper's output will continue to be stored in its current format.

## 4. Refactoring

*   The existing scraper logic will be refactored to be more modular and easily callable from the `main.py` CLI.
*   A new module, `curator.py`, will be created for the artist curation logic.