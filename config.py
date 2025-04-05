import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Config:
    BASE_URL = "https://m.kismia.com"
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    TOKEN_FILE = os.path.join(DATA_DIR, "auth_token.json")
    HIDS_FILE = os.path.join(DATA_DIR, "hids.json")
    PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
    
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    HIDS_FETCH_MAX_PAGES = 10000
    HIDS_PAGE_DELAY_MIN = 4
    HIDS_PAGE_DELAY_MAX = 7
    
    PROFILE_FETCH_DELAY_MIN = 1
    PROFILE_FETCH_DELAY_MAX = 3
    PROFILE_POLL_INTERVAL = 5 