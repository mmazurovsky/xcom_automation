"""
Configuration management for the Twitter automation service.
"""
import json
from typing import List, Dict
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class TwitterAccount:
    """Represents a Twitter account configuration."""

    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return f"TwitterAccount(username={self.username})"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB Configuration (DigitalOcean)
    mongo_user: str = Field(default="doadmin")
    mongo_password: str = Field(default="")
    mongo_host: str = Field(default="db-mongodb-fra1-53189-e46f01e8.mongo.ondigitalocean.com")
    mongo_port: int = Field(default=25060)
    mongo_db: str = Field(default="xcom_automation")

    # API Security
    api_key: str = Field(default="changeme")

    # Twitter Accounts (JSON string)
    twitter_accounts: str = Field(
        default='[{"username": "username", "email": "email@example.com", "password": "password"}]'
    )

    # Application Settings
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="info")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator("twitter_accounts")
    @classmethod
    def validate_twitter_accounts(cls, v: str) -> str:
        """Validate that twitter_accounts is valid JSON."""
        try:
            accounts = json.loads(v)
            if not isinstance(accounts, list):
                raise ValueError("TWITTER_ACCOUNTS must be a JSON array")
            for account in accounts:
                required_fields = ["username", "email", "password"]
                for field in required_fields:
                    if field not in account:
                        raise ValueError(f"Each account must have '{field}' field")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"TWITTER_ACCOUNTS must be valid JSON: {e}")

    def get_twitter_accounts(self) -> List[TwitterAccount]:
        """Parse and return Twitter account configurations."""
        accounts_data = json.loads(self.twitter_accounts)
        return [
            TwitterAccount(
                username=acc["username"],
                email=acc["email"],
                password=acc["password"]
            )
            for acc in accounts_data
        ]

    def get_account_by_username(self, username: str) -> TwitterAccount | None:
        """Get a specific Twitter account by username."""
        accounts = self.get_twitter_accounts()
        for account in accounts:
            if account.username == username:
                return account
        return None

    def get_mongo_uri(self) -> str:
        """Construct MongoDB connection URI for DigitalOcean."""
        # DigitalOcean MongoDB uses mongodb+srv:// with replica set
        return (
            f"mongodb+srv://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}/{self.mongo_db}"
            f"?authSource=admin&replicaSet=db-mongodb-fra1-53189&tls=true"
        )


# Global settings instance
settings = Settings()
