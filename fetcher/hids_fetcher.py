import time
import random
import logging
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config

logger = logging.getLogger(__name__)

class HidsFetcher(BaseFetcher):
    def __init__(self, auth_manager, max_pages=None, filename=None):
        filename = filename or Config.HIDS_FILE
        super().__init__(auth_manager, filename)
        self.base_url = f"{HttpConfig.BASE_URL}/v3/matchesGame/users:pickUp"
        self.max_pages = max_pages or Config.HIDS_FETCH_MAX_PAGES
        self.hids = []
        self.next_page_token = None
        self.load_existing_hids()

    def load_existing_hids(self):
        self.hids = self.load_from_file()

    def dump_hids(self):
        self.save_to_file(self.hids)

    def fetch(self):
        for page in range(self.max_pages):
            headers = self.get_headers({"x-client-data": "XbPVwbt9ro651,n2rVn1tyD069k,DJK6pat0XpVPn,J70RlrtM2GVlB"})
            if not headers:
                break

            url = self.base_url if not self.next_page_token else f"{self.base_url}?pageToken={self.next_page_token}"
            try:
                resp = self.make_request("GET", url, headers=headers, cookies=self.cookies)
                if resp.status_code != 200:
                    logger.error("Request failed with status: %d", resp.status_code)
                    break

                data = resp.json()
                hits = data.get("hits", [])
                hids_count_before = len(self.hids)
                for hit in hits:
                    hid = hit.get("user", {}).get("hid")
                    if hid and not any(h.get("id") == hid for h in self.hids):
                        self.hids.append({"id": hid, "processed": False})
                        
                new_hids_added = len(self.hids) > hids_count_before
                if new_hids_added:
                    logger.info("Added %d new HIDs", len(self.hids) - hids_count_before)
                    self.dump_hids()
                    
                logger.info("Page %d processed", page + 1)

                self.next_page_token = data.get("nextPageToken")
                if not self.next_page_token:
                    logger.info("No nextPageToken found; ending pagination.")
                    break
            except Exception as e:
                logger.error("Error fetching hids: %s", e)
                time.sleep(Config.RETRY_DELAY)
                continue

            time.sleep(random.uniform(Config.HIDS_PAGE_DELAY_MIN, Config.HIDS_PAGE_DELAY_MAX))
            
        if not any(new_hids_added for _ in range(self.max_pages)) and self.hids:
            self.dump_hids()
            
        return self.hids
