import time
import random
import logging
import json
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config

logger = logging.getLogger(__name__)

class ProfileFetcher(BaseFetcher):
    def __init__(self, auth_manager, filename=None, hids_file=None):
        filename = filename or Config.PROFILES_FILE
        self.hids_file = hids_file or Config.HIDS_FILE
        super().__init__(auth_manager, filename)
        self.base_url = f"{HttpConfig.BASE_URL}/rest/v2/user/info/profile"
        self.profiles = []
        self.load_existing_profiles()

    def load_existing_profiles(self):
        self.profiles = self.load_from_file([])

    def dump_profiles(self):
        self.save_to_file(self.profiles)

    def load_hids(self):
        try:
            with open(self.hids_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("No hids file found or file is empty: %s", self.hids_file)
            return []

    def save_hids(self, hids):
        try:
            with open(self.hids_file, "w") as f:
                json.dump(hids, f, indent=4)
        except Exception as e:
            logger.error("Failed to save hids to %s: %s", self.hids_file, e)

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

    def process_unprocessed_hids(self):
        hids = self.load_hids()
        processed_count = 0
        
        for hid_entry in hids:
            if not hid_entry.get("processed", False):
                hid = hid_entry.get("id")
                if not hid:
                    continue
                    
                profile = self.fetch_profile(hid)
                if profile:
                    self.profiles.append(profile)
                    hid_entry["processed"] = True
                    processed_count += 1
                    self.dump_profiles()
                    self.save_hids(hids)
                
                time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        
        logger.info("Processed %d new profiles", processed_count)
        return processed_count

    def continuous_fetch(self):
        while True:
            processed = self.process_unprocessed_hids()
            if processed == 0:
                logger.info("No new profiles to process, waiting...")
                time.sleep(Config.PROFILE_POLL_INTERVAL)  # Wait before checking again

    def fetch_profiles(self, hids):
        for hid in hids:
            profile = self.fetch_profile(hid)
            if profile:
                self.profiles.append(profile)
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        self.dump_profiles()
        return self.profiles
