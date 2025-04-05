import time
import requests
import json
import random
import logging

logger = logging.getLogger(__name__)

class ProfileFetcher:
    def __init__(self, auth_manager, filename="profiles.json"):
        self.auth_manager = auth_manager
        self.filename = filename
        self.base_url = "https://m.kismia.com/rest/v2/user/info/profile"
        self.cookies = {
            "lang": "en",
            "funnel_id": "67e91fc11b3915.24228280",
            "landing_user": "1743331265111"
        }
        self.profiles = []

    def update_headers(self):
        access_token = self.auth_manager.get_access_token()
        if not access_token:
            logger.error("Could not get a valid access token")
            return None
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US",
            "accept-version": "3.0",
            "authorization": f"JWT {access_token}",
            "cache-control": "no-cache",
            "platform": "mobile",
            "platform-version": "2",
            "priority": "u=1, i",
            "referer": "https://m.kismia.com/matches",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
            "x-client-version": "v3mobile-spa/2b5c480eb"
        }
        return headers

    def dump_profiles(self):
        with open(self.filename, "w") as f:
            json.dump(self.profiles, f, indent=4)
        logger.info("Profiles dumped to %s", self.filename)

    def fetch_profiles(self, hids):
        for hid in hids:
            headers = self.update_headers()
            if headers is None:
                logger.error("Skipping profile fetch due to missing headers.")
                continue

            params = {
                "data_group": "profile",
                "users_hids[]": hid
            }
            try:
                resp = requests.get(self.base_url, headers=headers, cookies=self.cookies, params=params)
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
            time.sleep(random.uniform(1, 3))
        self.dump_profiles()
        return self.profiles
