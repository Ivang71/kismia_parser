import os
import json
import time
import logging
import requests
from requests.exceptions import RequestException
import jwt
from utils import HttpConfig
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    TOKEN_FILE = Config.TOKEN_FILE
    REFRESH_ENDPOINT = f"{HttpConfig.BASE_URL}/rest/v2/login/refresh_token"
    
    def __init__(self):
        self.token_data = {}
        self.load_tokens()

    def load_tokens(self):
        if os.path.exists(self.TOKEN_FILE):
            try:
                with open(self.TOKEN_FILE, "r") as f:
                    self.token_data = json.load(f)
                logger.info("Tokens loaded from file.")
            except Exception as e:
                logger.error("Error reading token file: %s", e)
        else:
            logger.info("Token file not found. Please populate it with initial token data.")
    
    def save_tokens(self):
        try:
            with open(self.TOKEN_FILE, "w") as f:
                json.dump(self.token_data, f, indent=4)
            logger.info("Tokens saved to file.")
        except Exception as e:
            logger.error("Error saving token file: %s", e)
    
    def decode_token(self, token):
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error("Failed to decode JWT: %s", e)
            return None

    def is_token_expired(self, token):
        payload = self.decode_token(token)
        if not payload or "exp" not in payload:
            logger.error("Token payload invalid or missing 'exp'.")
            return True
        exp = payload["exp"]
        current_time = int(time.time())
        if current_time >= exp - 60:
            logger.info("Token expired or near expiry (current: %d, exp: %d).", current_time, exp)
            return True
        return False

    def refresh_tokens(self):
        if "refreshToken" not in self.token_data or "accessToken" not in self.token_data:
            logger.error("Missing tokens required for refresh.")
            return False

        payload = {
            "refresh_token": self.token_data["refreshToken"].get("refresh_token"),
            "access_token": self.token_data["accessToken"].get("access_token")
        }
        
        headers = HttpConfig.get_common_headers()
        headers["content-type"] = "application/json"
        
        retries = 0
        while retries < Config.MAX_RETRIES:
            try:
                logger.info("Refreshing tokens...")
                response = requests.post(
                    self.REFRESH_ENDPOINT, 
                    json=payload, 
                    headers=headers, 
                    timeout=Config.REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    if result:
                        self.token_data["refreshToken"] = result.get("refreshToken", {})
                        self.token_data["accessToken"] = result.get("accessToken", {})
                        self.token_data["authToken"] = result.get("authToken")
                        self.token_data["authKey"] = result.get("authKey")
                        self.save_tokens()
                        logger.info("Tokens refreshed successfully.")
                        return True
                    else:
                        logger.error("No 'result' in refresh response: %s", data)
                else:
                    logger.error("Refresh request failed with status code %d", response.status_code)
                break
            except RequestException as e:
                retries += 1
                logger.error("Error during token refresh (attempt %d/%d): %s", 
                            retries, Config.MAX_RETRIES, e)
                if retries >= Config.MAX_RETRIES:
                    break
                time.sleep(Config.RETRY_DELAY)
        
        return False

    def get_access_token(self):
        if "accessToken" not in self.token_data or "access_token" not in self.token_data["accessToken"]:
            logger.error("Access token not found in token data.")
            return None
        access_token = self.token_data["accessToken"]["access_token"]
        if self.is_token_expired(access_token):
            logger.info("Access token expired; refreshing.")
            if not self.refresh_tokens():
                logger.error("Failed to refresh tokens.")
                return None
            access_token = self.token_data["accessToken"].get("access_token")
        return access_token
