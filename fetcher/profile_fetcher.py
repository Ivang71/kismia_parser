import time
import random
import logging
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config
from db import Database

logger = logging.getLogger(__name__)

class ProfileFetcher(BaseFetcher):
    def __init__(self, auth_manager):
        super().__init__(auth_manager)
        self.base_url = f"{HttpConfig.BASE_URL}/rest/v2/user/info/profile"
        self.db = Database()

    def fetch_profile(self, hid):
        headers = self.get_headers({
            "accept-version": "3.0",
            "cache-control": "no-cache"
        })
        if not headers:
            return None

        params = {
            "data_group": "profile",
            "users_hids[]": hid
        }
        try:
            resp = self.make_request(
                "GET", 
                self.base_url, 
                headers=headers, 
                cookies=self.cookies, 
                params=params
            )
            if resp.status_code != 200:
                logger.error("Profile fetch failed for hid %s with status: %d", hid, resp.status_code)
                return None
            data = resp.json()
            if "result" in data and data["result"]:
                profile = data["result"][0]
                logger.info("Fetched profile for hid %s", hid)
                return profile
            else:
                logger.warning("No profile data for hid %s", hid)
        except Exception as e:
            logger.error("Exception while fetching profile for hid %s: %s", hid, e)
        return None

    def process_batch_items(self):
        users = self.db.get_users_without_profile(limit=50)
        processed_count = 0
        
        for hid, user_data in users:
            profile = self.fetch_profile(hid)
            if profile:
                if self.db.save_user_profile(hid, profile):
                    processed_count += 1
            
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        
        logger.info("Processed %d new profiles", processed_count)
        total_with_profile = self.db.count_users_with_profile()
        total_users = self.db.count_users()
        logger.info(f"Progress: {total_with_profile}/{total_users} profiles fetched")
        return processed_count

    def continuous_fetch(self):
        while True:
            processed = self.process_batch_items()
            if processed == 0:
                logger.info("No new profiles to process, waiting...")
                time.sleep(Config.PROFILE_POLL_INTERVAL)
