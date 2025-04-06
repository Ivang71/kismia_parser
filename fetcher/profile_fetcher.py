import time
import random
import logging
from utils import HttpConfig
from fetcher.base_fetcher import BaseFetcher
from config import Config
from db import Database
from fetcher.kismia_api import KismiaAPI

logger = logging.getLogger(__name__)

class ProfileFetcher:
    def __init__(self, auth_manager):
        self.api = KismiaAPI(auth_manager)
    
    def fetch_profile(self, hid):
        return self.api.fetch_user_profile(hid)
    
    def process_batch_items(self):
        return self.api.process_profiles_batch()
    
    def continuous_fetch(self):
        self.api.continuous_profile_fetch()
