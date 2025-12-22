import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    X_USER = os.getenv("X_USER")
    X_PASS = os.getenv("X_PASS")

    # Sleep Timers (in seconds)
    LOGIN_COOKIE_APPLY_DELAY = 5
    LOGIN_FORM_TRANSITION_DELAY = 5
    SCROLL_INITIAL_LOAD_DELAY = 20
    SCROLL_NEW_CONTENT_DELAY = 5

    if not X_USER or not X_PASS:
        raise ValueError("X_USER and X_PASS environment variables must be set in the .env file.")

config = Config()
