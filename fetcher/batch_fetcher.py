import time
import random
import logging
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config
from db import Database

logger = logging.getLogger(__name__)

class BatchFetcher(BaseFetcher):
    def __init__(self, auth_manager, max_pages=None):
        super().__init__(auth_manager)
        self.base_url = f"{HttpConfig.BASE_URL}/v3/matchesGame/users:pickUp"
        self.max_pages = max_pages or Config.HIDS_FETCH_MAX_PAGES
        self.next_page_token = None
        self.db = Database()

    def fetch(self):
        for page in range(self.max_pages):
            # Reset page token every 10 pages
            if page > 0 and page % 10 == 0:
                self.next_page_token = None
                logger.info("Resetting page token at page %d", page)
                
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
                saved_count = 0
                
                for hit in hits:
                    if self.db.save_user(hit):
                        saved_count += 1
                        
                if saved_count > 0:
                    logger.info("Added %d new items", saved_count)
                    
                logger.info("Page %d processed", page + 1)

                self.next_page_token = data.get("nextPageToken")
                if not self.next_page_token:
                    logger.info("No nextPageToken found; ending pagination.")
                    break
            except Exception as e:
                logger.error("Error fetching items: %s", e)
                time.sleep(Config.RETRY_DELAY)
                continue

            time.sleep(random.uniform(Config.HIDS_PAGE_DELAY_MIN, Config.HIDS_PAGE_DELAY_MAX))
        
        total_users = self.db.count_users()
        logger.info(f"Total users in database: {total_users}")
        return total_users
