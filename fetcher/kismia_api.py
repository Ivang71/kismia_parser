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
        
        # Load user data files
        self.passed_users_file = os.path.join(Config.DATA_DIR, "passed_users.json")
        self.liked_users_file = os.path.join(Config.DATA_DIR, "liked_users.json")
        self.passed_users = self._load_json_set(self.passed_users_file)
        self.liked_users = self._load_json_set(self.liked_users_file)
        self.like_probability = 0.5
    
    def _load_json_set(self, file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        return set()
    
    def _save_json_set(self, data_set, file_path):
        try:
            with open(file_path, "w") as f:
                json.dump(list(data_set), f)
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
    
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
            
        for attempt in range(Config.MAX_RETRIES):
            try:
                return requests.request(method, url, **kwargs)
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{Config.MAX_RETRIES}): {e}")
                if attempt >= Config.MAX_RETRIES - 1:
                    logger.error(f"Max retries reached for request to {url}")
                    raise
                time.sleep(Config.RETRY_DELAY)
    
    def pass_on_user(self, hid, tracking_data=None):
        if hid in self.passed_users:
            logger.info(f"Already passed on user {hid}")
            return True
            
        self.passed_users.add(hid)
        self._save_json_set(self.passed_users, self.passed_users_file)
        
        try:
            url = f"{self.base_url}/v3/matchesGame/users/{hid}:pass"
            headers = self.get_headers()
            if not headers:
                return False
                
            json_data = {"interactionMethod": "INTERACTION_METHOD_CLICK"}
            if tracking_data:
                json_data["trackingData"] = tracking_data
                logger.debug(f"Using tracking data for pass: {tracking_data}")
                
            resp = self.make_request("POST", url, headers=headers, cookies=self.cookies, json=json_data)
            logger.debug(f"Pass response for {hid}: status={resp.status_code}, body={resp.text[:200]}")
            
            if resp.status_code == 200:
                logger.info(f"Successfully passed on user {hid}")
            else:
                logger.info(f"API rejected pass for {hid} with status {resp.status_code}")
            return True
                
        except Exception as e:
            logger.error(f"Error attempting to pass on user {hid}: {e}")
            return True
    
    def like_user(self, hid, tracking_data=None):
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
            
            json_data = {"interactionMethod": "INTERACTION_METHOD_CLICK"}
            if tracking_data:
                json_data["trackingData"] = tracking_data
                logger.debug(f"Using tracking data for like: {tracking_data}")
            
            resp = self.make_request("POST", url, headers=headers, cookies=self.cookies, json=json_data)
            logger.debug(f"Like response for {hid}: status={resp.status_code}, body={resp.text[:200]}")
            
            if resp.status_code in [200, 400]:
                self.liked_users.add(hid)
                self._save_json_set(self.liked_users, self.liked_users_file)
                log_msg = "Successfully liked" if resp.status_code == 200 else "Like request sent to"
                logger.info(f"{log_msg} user {hid}")
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
            headers = self.get_headers({"x-client-data": "XbPVwbt9ro651,n2rVn1tyD069k,DJK6pat0XpVPn,WAjEdltM2eEKl,J70RlrtM2GVlB,1GyEaGtvGB6jB"})
            if not headers:
                break

            url = batch_url if not self.next_page_token else f"{batch_url}?pageToken={self.next_page_token}"
            try:
                resp = self.make_request("GET", url, headers=headers, cookies=self.cookies)
                if resp.status_code != 200:
                    logger.error(f"Request failed with status: {resp.status_code}")
                    break

                data = resp.json()
                hits = data.get("hits", [])
                logger.info(f"Fetched {len(hits)} users from batch API")
                
                stats = {"saved": 0, "passed": 0, "liked": 0, "skipped": 0}
                
                for hit in hits:
                    if self.db.save_user(hit):
                        stats["saved"] += 1
                    
                    if 'user' in hit and 'hid' in hit['user']:
                        hid = hit['user']['hid']
                        tracking_data = hit.get('trackingData')
                        
                        if hid in self.liked_users or hid in self.passed_users:
                            stats["skipped"] += 1
                            continue
                        
                        if random.random() < like_prob:
                            if self.like_user(hid, tracking_data):
                                stats["liked"] += 1
                        else:
                            if self.pass_on_user(hid, tracking_data):
                                stats["passed"] += 1
                        
                        time.sleep(random.uniform(0.5, 1.5))
                    
                logger.info(f"Added {stats['saved']} new items")
                logger.info(f"Liked {stats['liked']}, passed on {stats['passed']}, skipped {stats['skipped']} out of {len(hits)} users")
                logger.info(f"Page {page + 1} processed")

                self.next_page_token = data.get("nextPageToken")
                if not self.next_page_token:
                    logger.info("No nextPageToken found; ending pagination")
                    break
            except Exception as e:
                logger.error(f"Error fetching items: {e}")
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

        params = {"data_group": "profile", "users_hids[]": hid}
        
        try:
            resp = self.make_request("GET", profile_url, headers=headers, cookies=self.cookies, params=params)
            if resp.status_code != 200:
                logger.error(f"Profile fetch failed for hid {hid} with status: {resp.status_code}")
                return None
                
            data = resp.json()
            if "result" in data and data["result"]:
                profile = data["result"][0]
                logger.info(f"Fetched profile for hid {hid}")
                return profile
            else:
                logger.warning(f"No profile data for hid {hid}")
        except Exception as e:
            logger.error(f"Exception while fetching profile for hid {hid}: {e}")
        return None
    
    def process_profiles_batch(self, limit=50):
        users = self.db.get_users_without_profile(limit=limit)
        processed_count = 0
        
        for hid, user_data in users:
            profile = self.fetch_user_profile(hid)
            if profile and self.db.save_user_profile(hid, profile):
                processed_count += 1
            
            time.sleep(random.uniform(Config.PROFILE_FETCH_DELAY_MIN, Config.PROFILE_FETCH_DELAY_MAX))
        
        logger.info(f"Processed {processed_count} new profiles")
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