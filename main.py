import logging
import threading
from auth import AuthManager
from fetcher import HidsFetcher, ProfileFetcher

logger = logging.getLogger(__name__)

def main():
    auth_manager = AuthManager()
    
    user_fetcher = HidsFetcher(auth_manager)
    profile_fetcher = ProfileFetcher(auth_manager)
    
    # Start both fetchers in separate threads
    hids_thread = threading.Thread(target=user_fetcher.fetch, daemon=True)
    profile_thread = threading.Thread(target=profile_fetcher.continuous_fetch, daemon=True)
    
    logger.info("Starting HidsFetcher and ProfileFetcher in parallel")
    hids_thread.start()
    profile_thread.start()
    
    # Keep the main thread alive
    try:
        hids_thread.join()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")

if __name__ == "__main__":
    main()
