import logging
from config import Config

logger = logging.getLogger(__name__)

class HttpConfig:
    BASE_URL = Config.BASE_URL
    USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36"
    
    @staticmethod
    def get_common_cookies():
        return {
            "lang": "en",
            "funnel_id": "67e91fc11b3915.24228280",
            "landing_user": "1743331265111"
        }
    
    @staticmethod
    def get_common_headers(access_token=None):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US",
            "platform": "mobile",
            "platform-version": "2",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": HttpConfig.USER_AGENT,
            "x-client-version": "v3mobile-spa/2b5c480eb"
        }
        
        if access_token:
            headers["authorization"] = f"JWT {access_token}"
            
        return headers 