import logging
import requests
import time
import random
import json
import os
from utils import HttpConfig
from config import Config
from db import Database

logger = logging.getLogger(__name__)

class KismiaAPI:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.cookies = HttpConfig.get_common_cookies()
        self.db = Database()
        self.base_url = HttpConfig.BASE_URL
        self.next_page_token = None
        self.passed_users_file = os.path.join(Config.DATA_DIR, "passed_users.json")
        self.passed_users = self._load_passed_users()  # Track users we've passed on
        self.liked_users_file = os.path.join(Config.DATA_DIR, "liked_users.json")
        self.liked_users = self._load_liked_users()  # Track users we've liked
        self.like_probability = 0.5  # Default like probability
    
    def _load_passed_users(self):
        if os.path.exists(self.passed_users_file):
            try:
                with open(self.passed_users_file, "r") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading passed users file: {e}")
        return set()
    
    def _save_passed_users(self):
        try:
            with open(self.passed_users_file, "w") as f:
                json.dump(list(self.passed_users), f)
        except Exception as e:
            logger.error(f"Error saving passed users file: {e}")
    
    def _load_liked_users(self):
        if os.path.exists(self.liked_users_file):
            try:
                with open(self.liked_users_file, "r") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading liked users file: {e}")
        return set()
    
    def _save_liked_users(self):
        try:
            with open(self.liked_users_file, "w") as f:
                json.dump(list(self.liked_users), f)
        except Exception as e:
            logger.error(f"Error saving liked users file: {e}")
    
    def get_headers(self, additional_headers=None):
        access_token = self.auth_manager.get_access_token()
        if not access_token:
            logger.error("Could not get a valid access token")
            return None
            
        headers = HttpConfig.get_common_headers(access_token)
        headers["referer"] = f"{self.base_url}/matches"
        
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
    
    def pass_on_user(self, hid):
        # Skip if we've already passed on this user
        if hid in self.passed_users:
            logger.info(f"Already passed on user {hid}")
            return True
            
        # Despite API errors, consider the user passed for our tracking
        self.passed_users.add(hid)
        self._save_passed_users()
        logger.info(f"Marked user {hid} as passed")
        
        # Try the actual API pass call, but don't depend on its success
        try:
            url = f"{self.base_url}/v3/matchesGame/users/{hid}:pass"
            headers = self.get_headers()
            if not headers:
                return False
                
            json_data = {
                "interactionMethod": "INTERACTION_METHOD_CLICK"
            }
            
            resp = self.make_request("POST", url, headers=headers, cookies=self.cookies, json=json_data)
            if resp.status_code == 200:
                logger.info(f"Successfully passed on user {hid}")
                return True
            else:
                # Log the error but still consider it passed for our purposes
                logger.info(f"API rejected pass for {hid} with status {resp.status_code}")
                return True
                
        except Exception as e:
            logger.error(f"Error attempting to pass on user {hid}: {e}")
            return True  # Still consider it passed for our purposes
    
    def like_user(self, hid):
        # Skip if we've already liked this user
        if hid in self.liked_users:
            logger.info(f"Already liked user {hid}")
            return True
            
        try:
            url = f"{self.base_url}/v3/matchesGame/users/{hid}:like"
            
            headers = self.get_headers({
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "platform": "desktop",
                "platform-version": "2",
                "x-client-version": "desktop-spa/69b81e654",
                "priority": "u=1, i"
            })
            
            if not headers:
                return False
            
            # Use the known working tracking data from the curl example
            tracking_data = "ZmFsc2UtMC45OTU0ODg0ODM4NTE3NTE4LTE3NDM5MjE1OTItNDg="
            
            json_data = {
                "trackingData": tracking_data,
                "interactionMethod": "INTERACTION_METHOD_CLICK"
            }
            
            resp = self.make_request("POST", url, headers=headers, cookies=self.cookies, json=json_data)
            
            # For the purpose of our app, both 200 and 400 are considered successful
            # The API often returns 400 but the like is actually registered
            if resp.status_code in [200, 400]:
                self.liked_users.add(hid)
                self._save_liked_users()
                log_level = logger.info if resp.status_code == 200 else logger.warning
                log_level(f"{'Successfully liked' if resp.status_code == 200 else 'Like request sent to'} user {hid}")
                return True
            else:
                logger.error(f"API rejected like for {hid} with status {resp.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error attempting to like user {hid}: {e}")
            return False
    
    def fetch_batch_users(self, max_pages=None, like_probability=None):
        max_pages = max_pages or Config.HIDS_FETCH_MAX_PAGES
        like_prob = like_probability if like_probability is not None else self.like_probability
        batch_url = f"{self.base_url}/v3/matchesGame/users:pickUp"
        
        for page in range(max_pages):
            headers = self.get_headers({"x-client-data": "XbPVwbt9ro651,n2rVn1tyD069k,DJK6pat0XpVPn,J70RlrtM2GVlB"})
            if not headers:
                break

            url = batch_url if not self.next_page_token else f"{batch_url}?pageToken={self.next_page_token}"
            try:
                resp = self.make_request("GET", url, headers=headers, cookies=self.cookies)
                if resp.status_code != 200:
                    logger.error("Request failed with status: %d", resp.status_code)
                    break

                data = resp.json()
                hits = data.get("hits", [])
                logger.info(f"Fetched {len(hits)} users from batch API")
                
                saved_count = 0
                pass_count = 0
                like_count = 0
                skipped_count = 0
                
                for hit in hits:
                    if self.db.save_user(hit):
                        saved_count += 1
                    
                    # Extract HID from the nested user object
                    if 'user' in hit and 'hid' in hit['user']:
                        hid = hit['user']['hid']
                        logger.info(f"Processing user with HID: {hid}")
                        
                        # Skip if already liked or passed
                        if hid in self.liked_users or hid in self.passed_users:
                            logger.info(f"Skipping user {hid} - already processed")
                            skipped_count += 1
                            continue
                        
                        # Randomly decide to like or pass
                        if random.random() < like_prob:
                            if self.like_user(hid):
                                like_count += 1
                        else:
                            if self.pass_on_user(hid):
                                pass_count += 1
                        
                        time.sleep(random.uniform(0.5, 1.5))
                    else:
                        logger.warning(f"Could not find HID in hit structure")
                        
                if saved_count > 0:
                    logger.info("Added %d new items", saved_count)
                
                logger.info(f"Liked {like_count}, passed on {pass_count}, skipped {skipped_count} out of {len(hits)} users")
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
    
    def fetch_user_profile(self, hid):
        profile_url = f"{self.base_url}/rest/v2/user/info/profile"
        headers = self.get_headers({
            "accept-version": "3.0",
            "cache-control": "no-cache"
        })
        if not headers:
            return None

        params = {
            "data_group": "profile",
            "users_hids[]": hid
        }
        try:
            resp = self.make_request(
                "GET", 
                profile_url, 
                headers=headers, 
                cookies=self.cookies, 
                params=params
            )
            if resp.status_code != 200:
                logger.error("Profile fetch failed for hid %s with status: %d", hid, resp.status_code)
                return None
            data = resp.json()
            if "result" in data and data["result"]:
                profile = data["result"][0]
                logger.info("Fetched profile for hid %s", hid)
                return profile
            else:
                logger.warning("No profile data for hid %s", hid)
        except Exception as e:
            logger.error("Exception while fetching profile for hid %s: %s", hid, e)
        return None
    
    def process_profiles_batch(self, limit=50):
        users = self.db.get_users_without_profile(limit=limit)
        processed_count = 0
        
        for hid, user_data in users:
            profile = self.fetch_user_profile(hid)
            if profile:
                if self.db.save_user_profile(hid, profile):
                    processed_count += 1
            
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        
        logger.info("Processed %d new profiles", processed_count)
        total_with_profile = self.db.count_users_with_profile()
        total_users = self.db.count_users()
        logger.info(f"Progress: {total_with_profile}/{total_users} profiles fetched")
        return processed_count
    
    def continuous_profile_fetch(self):
        while True:
            processed = self.process_profiles_batch()
            if processed == 0:
                logger.info("No new profiles to process, waiting...")
                time.sleep(Config.PROFILE_POLL_INTERVAL) 