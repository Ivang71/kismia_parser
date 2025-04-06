import sqlite3
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DB_FILE
        self._init_db()
        
    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                hid TEXT PRIMARY KEY,
                data JSON NOT NULL,
                profile_detailed JSON
            )
            ''')
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def save_user(self, user_data):
        hid = user_data.get("user", {}).get("hid")
        if not hid:
            return False
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO users (hid, data) VALUES (?, ?)",
                    (hid, json.dumps(user_data))
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error saving user {hid}: {e}")
            return False
            
    def save_user_profile(self, hid, profile_data):
        if not hid or not profile_data:
            return False
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET profile_detailed = ? WHERE hid = ?",
                    (json.dumps(profile_data), hid)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error saving profile for user {hid}: {e}")
            return False
    
    def get_users_without_profile(self, limit=100):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT hid, data FROM users WHERE profile_detailed IS NULL LIMIT ?",
                    (limit,)
                )
                return [(row[0], json.loads(row[1])) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching users without profile: {e}")
            return []
            
    def get_all_users(self, limit=1000, offset=0):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT hid, data, profile_detailed FROM users LIMIT ? OFFSET ?",
                    (limit, offset)
                )
                result = []
                for row in cursor.fetchall():
                    user_data = json.loads(row[1])
                    if row[2]:
                        user_data["profile_detailed"] = json.loads(row[2])
                    result.append(user_data)
                return result
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
            
    def count_users(self, with_profile=False):
        query = "SELECT COUNT(*) FROM users"
        if with_profile:
            query += " WHERE profile_detailed IS NOT NULL"
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    def count_users_with_profile(self):
        return self.count_users(with_profile=True) 