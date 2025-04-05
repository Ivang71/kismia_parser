import logging
import requests
import time
from utils import HttpConfig
from config import Config

logger = logging.getLogger(__name__)

class BaseFetcher:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.cookies = HttpConfig.get_common_cookies()
        
    def get_headers(self, additional_headers=None):
        access_token = self.auth_manager.get_access_token()
        if not access_token:
            logger.error("Could not get a valid access token")
            return None
            
        headers = HttpConfig.get_common_headers(access_token)
        headers["referer"] = f"{HttpConfig.BASE_URL}/matches"
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def make_request(self, method, url, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = Config.REQUEST_TIMEOUT
            
        retries = 0
        while retries < Config.MAX_RETRIES:
            try:
                response = requests.request(method, url, **kwargs)
                return response
            except requests.RequestException as e:
                retries += 1
                logger.warning(f"Request failed (attempt {retries}/{Config.MAX_RETRIES}): {e}")
                if retries >= Config.MAX_RETRIES:
                    logger.error(f"Max retries reached for request to {url}")
                    raise
                time.sleep(Config.RETRY_DELAY) 