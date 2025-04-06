import logging
from fetcher.kismia_api import KismiaAPI

logger = logging.getLogger(__name__)

class BatchFetcher:
    def __init__(self, auth_manager, max_pages=None):
        self.api = KismiaAPI(auth_manager)
        self.max_pages = max_pages

    def fetch(self):
        return self.api.fetch_batch_users(max_pages=self.max_pages)
