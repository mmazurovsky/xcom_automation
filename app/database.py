"""
MongoDB operations for storing Twitter session cookies.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from app.config import settings

logger = logging.getLogger(__name__)


class CookieDatabase:
    """Handles MongoDB operations for Twitter session cookies."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.sessions_collection = None

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            mongo_uri = settings.get_mongo_uri()
            self.client = MongoClient(mongo_uri)
            self.db = self.client[settings.mongo_db]
            self.sessions_collection = self.db["twitter_sessions"]

            # Create index on username for faster lookups
            self.sessions_collection.create_index("username", unique=True)

            logger.info(f"Connected to MongoDB: {settings.mongo_db}")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def save_cookies(self, username: str, cookies: Dict[str, Any]) -> bool:
        """
        Save or update cookies for a Twitter account.

        Args:
            username: Twitter username
            cookies: Cookie dictionary from twikit client

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session_data = {
                "username": username,
                "cookies": cookies,
                "updated_at": datetime.utcnow()
            }

            result = self.sessions_collection.update_one(
                {"username": username},
                {"$set": session_data},
                upsert=True
            )

            logger.info(f"Saved cookies for account: {username}")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to save cookies for {username}: {e}")
            return False

    def load_cookies(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Load cookies for a Twitter account.

        Args:
            username: Twitter username

        Returns:
            Cookie dictionary if found, None otherwise
        """
        try:
            session = self.sessions_collection.find_one({"username": username})

            if session and "cookies" in session:
                logger.info(f"Loaded cookies for account: {username}")
                return session["cookies"]

            logger.warning(f"No cookies found for account: {username}")
            return None
        except PyMongoError as e:
            logger.error(f"Failed to load cookies for {username}: {e}")
            return None

    def delete_cookies(self, username: str) -> bool:
        """
        Delete cookies for a Twitter account.

        Args:
            username: Twitter username

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.sessions_collection.delete_one({"username": username})

            if result.deleted_count > 0:
                logger.info(f"Deleted cookies for account: {username}")
                return True
            else:
                logger.warning(f"No cookies found to delete for account: {username}")
                return False
        except PyMongoError as e:
            logger.error(f"Failed to delete cookies for {username}: {e}")
            return False

    def get_all_usernames(self) -> list[str]:
        """
        Get list of all Twitter usernames with stored sessions.

        Returns:
            List of usernames
        """
        try:
            sessions = self.sessions_collection.find({}, {"username": 1})
            return [session["username"] for session in sessions]
        except PyMongoError as e:
            logger.error(f"Failed to retrieve usernames: {e}")
            return []


# Global database instance
cookie_db = CookieDatabase()
