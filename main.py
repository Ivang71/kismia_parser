import logging
from auth import AuthManager
from fetcher import HidsFetcher, ProfileFetcher

logger = logging.getLogger(__name__)

def main():
    auth_manager = AuthManager()
    
    user_fetcher = HidsFetcher(auth_manager)
    hids = user_fetcher.fetch()
    logger.info("Total hids fetched: %d", len(hids))
    
    if not hids:
        logger.error("No hids found; exiting.")
        return

    profile_fetcher = ProfileFetcher(auth_manager)
    profiles = profile_fetcher.fetch_profiles(hids)
    logger.info("Total profiles fetched: %d", len(profiles))

if __name__ == "__main__":
    main()
