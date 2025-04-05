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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            hid TEXT PRIMARY KEY,
            data JSON NOT NULL,
            profile_detailed JSON
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def save_user(self, user_data):
        hid = user_data.get("user", {}).get("hid")
        if not hid:
            return False
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (hid, data) VALUES (?, ?)",
                (hid, json.dumps(user_data))
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error saving user {hid}: {e}")
            return False
        finally:
            conn.close()
            
    def save_user_profile(self, hid, profile_data):
        if not hid or not profile_data:
            return False
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE users SET profile_detailed = ? WHERE hid = ?",
                (json.dumps(profile_data), hid)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error saving profile for user {hid}: {e}")
            return False
        finally:
            conn.close()
    
    def get_users_without_profile(self, limit=100):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT hid, data FROM users WHERE profile_detailed IS NULL LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [(row[0], json.loads(row[1])) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching users without profile: {e}")
            return []
        finally:
            conn.close()
            
    def get_all_users(self, limit=1000, offset=0):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT hid, data, profile_detailed FROM users LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                user_data = json.loads(row[1])
                if row[2]:  # If profile_detailed exists
                    user_data["profile_detailed"] = json.loads(row[2])
                result.append(user_data)
            return result
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
        finally:
            conn.close()
            
    def count_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
        finally:
            conn.close()
            
    def count_users_with_profile(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE profile_detailed IS NOT NULL")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting users with profile: {e}")
            return 0
        finally:
            conn.close() 