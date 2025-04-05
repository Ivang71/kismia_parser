import logging
import threading
from auth import AuthManager
from fetcher import BatchFetcher, ProfileFetcher
from db import Database

logger = logging.getLogger(__name__)

def main():
    auth_manager = AuthManager()
    db = Database()
    
    batch_fetcher = BatchFetcher(auth_manager)
    profile_fetcher = ProfileFetcher(auth_manager)
    
    logger.info(f"Starting with {db.count_users()} users in database")
    logger.info(f"Users with profiles: {db.count_users_with_profile()}")
    
    # Start both fetchers in separate threads
    batch_thread = threading.Thread(target=batch_fetcher.fetch, daemon=True)
    profile_thread = threading.Thread(target=profile_fetcher.continuous_fetch, daemon=True)
    
    logger.info("Starting BatchFetcher and ProfileFetcher in parallel")
    batch_thread.start()
    profile_thread.start()
    
    # Keep the main thread alive
    try:
        batch_thread.join()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")

if __name__ == "__main__":
    main()
