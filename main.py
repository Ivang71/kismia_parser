import logging
import threading
from auth import AuthManager
from fetcher import BatchFetcher, ProfileFetcher

logger = logging.getLogger(__name__)

def main():
    auth_manager = AuthManager()
    
    batch_fetcher = BatchFetcher(auth_manager)
    profile_fetcher = ProfileFetcher(auth_manager)
    
    batch_thread = threading.Thread(target=batch_fetcher.fetch, daemon=True)
    profile_thread = threading.Thread(target=profile_fetcher.continuous_fetch, daemon=True)
    
    batch_thread.start()
    profile_thread.start()
    
    try:
        batch_thread.join()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")

if __name__ == "__main__":
    main()
