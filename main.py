import logging
from auth.auth_manager import AuthManager
from fetcher.hids_fetcher import HidsFetcher
from fetcher.profile_fetcher import ProfileFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize the auth manager
    auth_manager = AuthManager()
    
    # Fetch user hids
    user_fetcher = HidsFetcher(auth_manager)
    hids = user_fetcher.fetch()
    logger.info("Total hids fetched: %d", len(hids))
    
    if not hids:
        logger.error("No hids found; exiting.")
        return

    # Use the hids to fetch full profiles
    profile_fetcher = ProfileFetcher(auth_manager)
    profiles = profile_fetcher.fetch_profiles(hids)
    logger.info("Total profiles fetched: %d", len(profiles))

if __name__ == "__main__":
    main()
