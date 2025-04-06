import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def merge_databases():
    source_conn = sqlite3.connect('kismia_to_merge.db')
    target_conn = sqlite3.connect('kismia.db')
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        source_cursor.execute("SELECT hid, data, profile_detailed FROM users")
        source_users = source_cursor.fetchall()
        
        target_cursor.execute("SELECT hid FROM users")
        existing_hids = {row[0] for row in target_cursor.fetchall()}
        
        new_users = [user for user in source_users if user[0] not in existing_hids]
        
        if new_users:
            logging.info(f"Adding {len(new_users)} new users to kismia.db")
            target_cursor.executemany(
                "INSERT INTO users (hid, data, profile_detailed) VALUES (?, ?, ?)",
                new_users
            )
            target_conn.commit()
            logging.info("Merge completed successfully")
        else:
            logging.info("No new users to add")
            
    except Exception as e:
        logging.error(f"Error during merge: {e}")
        target_conn.rollback()
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    merge_databases() 