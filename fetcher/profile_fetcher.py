import time
import random
import logging
import json
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config

logger = logging.getLogger(__name__)

class ProfileFetcher(BaseFetcher):
    def __init__(self, auth_manager, filename=None):
        filename = filename or Config.BATCH_FILE
        super().__init__(auth_manager, filename)
        self.base_url = f"{HttpConfig.BASE_URL}/rest/v2/user/info/profile"

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
        batch_data = self.load_from_file([])
        processed_count = 0
        
        for item in batch_data:
            hid = item.get("user", {}).get("hid")
            if not hid or "profile_detailed" in item:
                continue
                
            profile = self.fetch_profile(hid)
            if profile:
                item["profile_detailed"] = profile
                processed_count += 1
                self.save_to_file(batch_data)
            
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        
        logger.info("Processed %d new profiles", processed_count)
        return processed_count

    def continuous_fetch(self):
        while True:
            processed = self.process_batch_items()
            if processed == 0:
                logger.info("No new profiles to process, waiting...")
                time.sleep(Config.PROFILE_POLL_INTERVAL)
