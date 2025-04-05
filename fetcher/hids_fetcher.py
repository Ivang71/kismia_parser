import time
import requests
import random
import json
import logging

logger = logging.getLogger(__name__)

class HidsFetcher:
    def __init__(self, auth_manager, max_pages=10000, filename="hids.json"):
        self.auth_manager = auth_manager
        self.base_url = "https://m.kismia.com/v3/matchesGame/users:pickUp"
        self.filename = filename
        self.max_pages = max_pages
        self.cookies = {
            "lang": "en",
            "funnel_id": "67e91fc11b3915.24228280",
            "landing_user": "1743331265111"
        }
        self.hids = []
        self.next_page_token = None
        self.load_existing_hids()

    def load_existing_hids(self):
        try:
            with open(self.filename, "r") as f:
                self.hids = json.load(f)
            logger.info("Loaded %d existing HIDs from %s", len(self.hids), self.filename)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No existing HIDs file found or file is empty. Starting fresh.")
            self.hids = []

    def dump_hids(self):
        with open(self.filename, "w") as f:
            json.dump(self.hids, f, indent=4)
        logger.info("HIDs dumped to %s", self.filename)

    def update_headers(self):
        access_token = self.auth_manager.get_access_token()
        if not access_token:
            logger.error("Could not get a valid access token")
            return None
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US",
            "authorization": f"JWT {access_token}",
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
            "x-client-data": "XbPVwbt9ro651,n2rVn1tyD069k,DJK6pat0XpVPn,J70RlrtM2GVlB",
            "x-client-version": "v3mobile-spa/f9c69e266"
        }
        return headers

    def fetch(self):
        for page in range(self.max_pages):
            headers = self.update_headers()
            if headers is None:
                logger.error("Skipping request due to missing headers.")
                break

            url = self.base_url if not self.next_page_token else f"{self.base_url}?pageToken={self.next_page_token}"
            resp = requests.get(url, headers=headers, cookies=self.cookies)
            if resp.status_code != 200:
                logger.error("Request failed with status: %d", resp.status_code)
                break

            data = resp.json()
            hits = data.get("hits", [])
            hids_count_before = len(self.hids)
            for hit in hits:
                hid = hit.get("user", {}).get("hid")
                if hid and hid not in self.hids:
                    self.hids.append(hid)
                    
            new_hids_added = len(self.hids) > hids_count_before
            if new_hids_added:
                logger.info("Added %d new HIDs", len(self.hids) - hids_count_before)
                self.dump_hids()
                
            logger.info("Page %d processed", page + 1)

            self.next_page_token = data.get("nextPageToken")
            if not self.next_page_token:
                logger.info("No nextPageToken found; ending pagination.")
                break

            time.sleep(random.uniform(7, 13))
            
        if not any(new_hids_added for _ in range(self.max_pages)) and self.hids:
            self.dump_hids()
            
        return self.hids
