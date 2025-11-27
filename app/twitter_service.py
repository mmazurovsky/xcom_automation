"""
Twitter service using Twikit library with retry logic and session management.
"""
import logging
from typing import Optional, Dict, List
from twikit import Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.config import settings, TwitterAccount
from app.database import cookie_db

logger = logging.getLogger(__name__)


class TwitterService:
    """Manages Twitter client instances and handles tweet posting."""

    def __init__(self):
        """Initialize the Twitter service."""
        self.clients: Dict[str, Client] = {}

    async def initialize_accounts(self):
        """
        Initialize Twitter client for all configured accounts.
        Load existing sessions or authenticate if needed.
        Also initializes accounts that have cookies in MongoDB but no credentials.
        """
        # First, initialize accounts with credentials
        accounts = settings.get_twitter_accounts()
        logger.info(f"Initializing {len(accounts)} configured account(s)...")

        initialized_usernames = set()
        for account in accounts:
            try:
                await self._initialize_account(account)
                initialized_usernames.add(account.username)
            except Exception as e:
                logger.error(f"Failed to initialize account {account.username}: {e}")
                # Continue with other accounts even if one fails

        # Then, initialize accounts that have cookies in MongoDB but no credentials
        db_usernames = cookie_db.get_all_usernames()
        cookie_only_accounts = [u for u in db_usernames if u not in initialized_usernames]

        if cookie_only_accounts:
            logger.info(f"Initializing {len(cookie_only_accounts)} account(s) from cookies only...")
            for username in cookie_only_accounts:
                try:
                    success = await self.initialize_from_cookies(username)
                    if success:
                        initialized_usernames.add(username)
                except Exception as e:
                    logger.error(f"Failed to initialize account {username} from cookies: {e}")

        logger.info(f"Total initialized accounts: {len(initialized_usernames)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def _initialize_account(self, account: TwitterAccount):
        """
        Initialize a single Twitter account with retry logic.

        Args:
            account: TwitterAccount configuration
        """
        logger.info(f"Initializing account: {account.username}")

        # Get proxy URL from settings
        proxy_url = settings.get_proxy_url()
        if proxy_url:
            logger.info(f"Using proxy for account {account.username}")
            client = Client('en-US', proxy=proxy_url)
        else:
            logger.warning(f"No proxy configured - using direct connection for {account.username}")
            client = Client('en-US')

        # Try to load existing cookies from MongoDB
        cookies = cookie_db.load_cookies(account.username)

        if cookies:
            try:
                # Load cookies into client
                client.set_cookies(cookies)
                logger.info(f"Loaded session from database for: {account.username}")
            except Exception as e:
                logger.warning(f"Failed to load cookies for {account.username}: {e}")
                cookies = None

        # If no cookies or loading failed, perform fresh authentication
        if not cookies:
            logger.info(f"Performing fresh authentication for: {account.username}")
            await client.login(
                auth_info_1=account.username,
                auth_info_2=account.email,
                password=account.password
            )

            # Save cookies to MongoDB
            new_cookies = client.get_cookies()
            cookie_db.save_cookies(account.username, new_cookies)
            logger.info(f"Authenticated and saved session for: {account.username}")

        # Store client instance
        self.clients[account.username] = client
        logger.info(f"Account {account.username} initialized successfully")

    async def refresh_session(self, username: str) -> bool:
        """
        Force re-authentication for a specific account.

        Args:
            username: Twitter username

        Returns:
            bool: True if successful, False otherwise
        """
        account = settings.get_account_by_username(username)
        if not account:
            logger.error(f"Account not found: {username}")
            return False

        try:
            # Delete old cookies
            cookie_db.delete_cookies(username)

            # Re-initialize account
            await self._initialize_account(account)
            return True
        except Exception as e:
            logger.error(f"Failed to refresh session for {username}: {e}")
            return False

    def reload_cookies_from_db(self, username: str) -> bool:
        """
        Reload cookies from MongoDB into the in-memory client.
        Creates a fresh client instance to ensure no stale cookie state.

        Args:
            username: Twitter username

        Returns:
            bool: True if successful, False otherwise
        """
        if username not in self.clients:
            logger.debug(f"Account {username} not in clients, skipping reload")
            return False

        try:
            # Load cookies from MongoDB
            cookies = cookie_db.load_cookies(username)

            if not cookies:
                logger.error(f"No cookies found in database for {username}")
                return False

            # Create fresh client to ensure no stale cookie state
            proxy_url = settings.get_proxy_url()
            if proxy_url:
                new_client = Client('en-US', proxy=proxy_url)
            else:
                new_client = Client('en-US')

            # Set cookies in the fresh client
            new_client.set_cookies(cookies)

            # Replace old client with new one
            self.clients[username] = new_client
            logger.info(f"Reloaded cookies with fresh client for: {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to reload cookies for {username}: {e}")
            return False

    async def initialize_from_cookies(self, username: str) -> bool:
        """
        Initialize an account using cookies from the database.
        Use this when you have cookies but no email/password credentials.

        Args:
            username: Twitter username

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"[INIT] Starting initialization for {username} from cookies")

            # Load cookies from MongoDB
            cookies = cookie_db.load_cookies(username)

            if not cookies:
                logger.error(f"[INIT] FAILED - No cookies found in database for {username}")
                return False

            # Create client with proxy if configured
            proxy_url = settings.get_proxy_url()
            if proxy_url:
                logger.info(f"[INIT] Using proxy for account {username}")
                client = Client('en-US', proxy=proxy_url)
            else:
                logger.warning(f"[INIT] No proxy configured - using direct connection for {username}")
                client = Client('en-US')

            # Set cookies in the client
            client.set_cookies(cookies)
            logger.info(f"[INIT] Cookies set in client for {username}")

            # Make a verification call to initialize client's internal state
            # This triggers the transaction system initialization
            try:
                user = await client.user_by_screen_name(username)
                logger.info(f"[INIT] Session verified for {username}: {user.name}")
            except Exception as verify_error:
                logger.info(f"[INIT] Skipping session verification for {username} (not critical): {verify_error}")
                # Continue anyway - cookies should still work for posting

            # Store client instance
            self.clients[username] = client
            logger.info(f"[INIT] ✓ Account {username} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[INIT] ✗ FAILED to initialize account {username}: {e}", exc_info=True)
            return False

    def get_client(self, username: str) -> Optional[Client]:
        """
        Get Twitter client for a specific account.

        Args:
            username: Twitter username

        Returns:
            Client instance if found, None otherwise
        """
        return self.clients.get(username)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def post_tweet(
        self,
        username: str,
        text: str,
        media_ids: Optional[List[str]] = None
    ) -> str:
        """
        Post a tweet on behalf of the specified account with retry logic.

        Args:
            username: Twitter username
            text: Tweet text content
            media_ids: Optional list of media IDs

        Returns:
            Tweet ID if successful

        Raises:
            ValueError: If account not found or not initialized
            Exception: If tweet posting fails after retries
        """
        client = self.get_client(username)

        if not client:
            raise ValueError(f"Account not initialized: {username}")

        try:
            logger.info(f"Posting tweet for account {username}: {text[:50]}...")

            # Post tweet
            tweet = await client.create_tweet(
                text=text,
                media_ids=media_ids
            )

            tweet_id = tweet.id
            logger.info(f"Tweet posted successfully: {tweet_id}")
            return tweet_id

        except Exception as e:
            logger.error(f"Failed to post tweet for {username}: {e}")

            # If authentication issue, try to refresh session
            if "auth" in str(e).lower() or "login" in str(e).lower():
                logger.info(f"Authentication issue detected, refreshing session for {username}")
                await self.refresh_session(username)

            raise

    async def upload_media(self, username: str, file_path: str) -> str:
        """
        Upload media file for a specific account.

        Args:
            username: Twitter username
            file_path: Path to media file

        Returns:
            Media ID

        Raises:
            ValueError: If account not found or not initialized
            Exception: If upload fails
        """
        client = self.get_client(username)

        if not client:
            raise ValueError(f"Account not initialized: {username}")

        try:
            logger.info(f"Uploading media for account {username}: {file_path}")
            media_id = await client.upload_media(file_path)
            logger.info(f"Media uploaded successfully: {media_id}")
            return media_id
        except Exception as e:
            logger.error(f"Failed to upload media for {username}: {e}")
            raise

    def get_initialized_accounts(self) -> List[str]:
        """
        Get list of initialized Twitter usernames.

        Returns:
            List of usernames
        """
        return list(self.clients.keys())


# Global Twitter service instance
twitter_service = TwitterService()
