# X Scraper 🐦

A Python-based scraper for downloading tweets and media from your personal X (formerly Twitter) "For You" timeline.

## Features ✨

- Scrapes tweets from the "For You" timeline. 📝
- Downloads associated media (images and videos). 📸🎬
- Saves tweet data (ID, author, text, stats) to a `tweets.jsonl` file. 💾
- Organizes output into timestamped directories for each run. 📁
- Handles login via credentials or session cookies. 🔑
- Configurable settings for delays and run duration. ⚙️
- Uses `undetected-chromedriver` to better avoid bot detection. 🕵️‍♂️

## Setup & Installation ⬇️

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd x-scraper
    ```

2.  **Set up a Python virtual environment:** 🐍
    It is highly recommended to use a virtual environment to manage dependencies.

    ```bash
    # Ensure you have Python 3.12+ installed
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:** 📦
    Install all required packages from `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

## Configuration 🛠️

1.  **Credentials:** 🔒
    Create a `.env` file in the root of the project directory. This file will store your X login credentials. **This file is ignored by Git and should never be committed.**

    ```
    # .env
    X_USER="your_x_username"
    X_PASS="your_x_password"
    ```

2.  **Delays (Optional):** ⏳
    You can fine-tune the script's behavior by adjusting the delay timers in `config.py`. These delays help mimic human behavior and can make the scraper more stable.

## Usage 🚀

The main entry point for the scraper is `main.py`.

### First-Time Run (Cookie Generation) 🍪

X employs strong bot detection that can block automated logins. To work around this, it's best to perform a one-time manual login to generate a `cookies.json` file. The script will use this file for subsequent runs to bypass the login screen.

1.  Run the script without the `--headless` flag. A Chrome window will open.
    ```bash
    python main.py --max-tweets 1
    ```
2.  In the browser window, log in to your X account. You may need to solve a CAPTCHA or other verification challenge. The script has a long timeout to give you time to do this.
3.  Once you successfully log in, the script will perform a very short scrape and create a `cookies.json` file in the project root.

Alternatively, you can manually create the `cookies.json` file by exporting cookies from your browser.

### Standard Usage 🟢

Once `cookies.json` exists, you can run the scraper headlessly.

```bash
python main.py --headless --max-tweets 100 --max-minutes 15 --output-dir ./scraped_data
```

### Command-Line Arguments 💻

-   `--max-tweets`: (Optional) The maximum number of tweets to scrape. Defaults to 50.
-   `--max-minutes`: (Optional) The maximum number of minutes to run the scraper. Defaults to 5.
-   `--output-dir`: (Optional) The base directory to save the output. Defaults to `output`.
-   `--headless`: (Optional) A flag to run the browser in headless mode (no UI). Recommended for standard runs after cookie generation.

## Output Structure 📂

The script creates a new timestamped directory for each run inside the specified `--output-dir`.

```
<output-dir>/
└── 20251222_103000/
    ├── media/
    │   ├── <media_file_1>.jpg
    │   └── <media_file_2>.mp4
    └── tweets.jsonl
```

-   **`tweets.jsonl`**: A [JSON Lines](https://jsonlines.org/) file where each line is a JSON object representing a scraped tweet and its metadata.
-   **`media/`**: A folder containing all the downloaded images and videos from the scraped tweets.
