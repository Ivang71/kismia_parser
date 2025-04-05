import time
import random
import logging
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config

logger = logging.getLogger(__name__)

class ProfileFetcher(BaseFetcher):
    def __init__(self, auth_manager, filename=None):
        filename = filename or Config.PROFILES_FILE
        super().__init__(auth_manager, filename)
        self.base_url = f"{HttpConfig.BASE_URL}/rest/v2/user/info/profile"
        self.profiles = []

    def dump_profiles(self):
        self.save_to_file(self.profiles)

    def fetch_profiles(self, hids):
        for hid in hids:
            headers = self.get_headers({
                "accept-version": "3.0",
                "cache-control": "no-cache"
            })
            if not headers:
                continue

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
                    continue
                data = resp.json()
                if "result" in data and data["result"]:
                    self.profiles.append(data["result"][0])
                    logger.info("Fetched profile for hid %s", hid)
                else:
                    logger.warning("No profile data for hid %s", hid)
            except Exception as e:
                logger.error("Exception while fetching profile for hid %s: %s", hid, e)
                time.sleep(Config.RETRY_DELAY)
                continue
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        self.dump_profiles()
        return self.profiles
