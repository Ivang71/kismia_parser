import logging
import threading
from auth import AuthManager
from fetcher import KismiaAPI
from db import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    auth_manager = AuthManager()
    db = Database()
    api = KismiaAPI(auth_manager)
    
    logger.info(f"Starting with {db.count_users()} users in database")
    logger.info(f"Users with profiles: {db.count_users_with_profile()}")
    
    # batch_thread = threading.Thread(target=api.fetch_batch_users, daemon=True)
    profile_thread = threading.Thread(target=api.continuous_profile_fetch, daemon=True)

    # batch_thread.start()
    profile_thread.start()
    
    try:
        # batch_thread.join() only one at a time
        profile_thread.join()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")

if __name__ == "__main__":
    main()
