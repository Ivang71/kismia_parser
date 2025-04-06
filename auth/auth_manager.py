import os
import json
import time
import logging
import requests
from requests.exceptions import RequestException
import jwt
import subprocess
from utils import HttpConfig
from config import Config

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.token_file = Config.TOKEN_FILE
        self.refresh_endpoint = f"{HttpConfig.BASE_URL}/rest/v2/login/refresh_token"
        self.token_data = {}
        self.load_tokens()

    def load_tokens(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    self.token_data = json.load(f)
                logger.info("Tokens loaded from file")
            except Exception as e:
                logger.error(f"Error reading token file: {e}")
        else:
            logger.info("Token file not found. Please populate it with initial token data")
    
    def save_tokens(self):
        try:
            with open(self.token_file, "w") as f:
                json.dump(self.token_data, f, indent=4)
            logger.info("Tokens saved to file")
        except Exception as e:
            logger.error(f"Error saving token file: {e}")
    
    def decode_token(self, token):
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Failed to decode JWT: {e}")
            return None

    def is_token_expired(self, token):
        payload = self.decode_token(token)
        if not payload or "exp" not in payload:
            logger.error("Token payload invalid or missing 'exp'")
            return True
        exp = payload["exp"]
        current_time = int(time.time())
        return current_time >= exp - 60

    def refresh_tokens(self):
        if "refreshToken" not in self.token_data or "accessToken" not in self.token_data:
            logger.error("Missing tokens required for refresh")
            return False

        refresh_token = self.token_data["refreshToken"].get("refresh_token")
        access_token = self.token_data["accessToken"].get("access_token")
        
        if not refresh_token or not access_token:
            logger.error("Invalid token data for refresh")
            return False
        
        auth_token = self.token_data.get("authToken", "")
        
        curl_command = (
            f"curl '{self.refresh_endpoint}' "
            "-H 'accept: application/json, text/plain, */*' "
            "-H 'accept-language: en-US,en;q=0.9,ru;q=0.8' "
            "-H 'cache-control: no-cache' "
            "-H 'content-type: application/json' "
            f"-b 'pauth={auth_token}' "
            "-H 'dnt: 1' "
            f"-H 'origin: {HttpConfig.BASE_URL}' "
            "-H 'platform: mobile' "
            "-H 'platform-version: 2' "
            "-H 'pragma: no-cache' "
            "-H 'priority: u=1, i' "
            f"-H 'referer: {HttpConfig.BASE_URL}/matches' "
            "-H 'sec-ch-ua: \"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"' "
            "-H 'sec-ch-ua-mobile: ?1' "
            "-H 'sec-ch-ua-platform: \"Android\"' "
            "-H 'sec-fetch-dest: empty' "
            "-H 'sec-fetch-mode: cors' "
            "-H 'sec-fetch-site: same-origin' "
            "-H 'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36' "
            "-H 'x-client-version: v3mobile-spa/2b5c480eb' "
            f"--data-raw '{{\"refresh_token\":\"{refresh_token}\",\"access_token\":\"{access_token}\"}}'"
        )
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.info("Refreshing tokens...")
                result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        result_data = data.get("result", {})
                        if result_data:
                            self.token_data["refreshToken"] = result_data.get("refreshToken", {})
                            self.token_data["accessToken"] = result_data.get("accessToken", {})
                            self.token_data["authToken"] = result_data.get("authToken")
                            self.token_data["authKey"] = result_data.get("authKey")
                            self.save_tokens()
                            logger.info("Tokens refreshed successfully")
                            return True
                        else:
                            logger.error(f"No 'result' in refresh response: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse refresh response: {e}")
                else:
                    logger.error(f"Refresh request failed: {result.stderr}")
                break
            except Exception as e:
                logger.error(f"Error during token refresh (attempt {attempt+1}/{Config.MAX_RETRIES}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)
        
        return False

    def get_access_token(self):
        if "accessToken" not in self.token_data or "access_token" not in self.token_data["accessToken"]:
            logger.error("Access token not found in token data")
            return None
        access_token = self.token_data["accessToken"]["access_token"]
        if self.is_token_expired(access_token):
            logger.info("Access token expired; refreshing")
            if not self.refresh_tokens():
                logger.error("Failed to refresh tokens")
                return None
            access_token = self.token_data["accessToken"].get("access_token")
        return access_token
