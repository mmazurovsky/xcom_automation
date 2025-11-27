"""
Pydantic models for API request and response validation.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class TweetRequest(BaseModel):
    """Request model for posting a tweet."""

    username: str = Field(
        ...,
        description="Twitter username of the account to use"
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Tweet text content (URLs will be automatically detected and linkified by Twitter)"
    )
    media_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of media IDs to attach to the tweet"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "applyfirst_app",
                "text": "Check out this awesome article! https://example.com/article",
                "media_ids": None
            }
        }


class TweetResponse(BaseModel):
    """Response model for tweet posting."""

    success: bool = Field(..., description="Whether the tweet was posted successfully")
    message: str = Field(..., description="Status message")
    tweet_id: Optional[str] = Field(
        default=None,
        description="Twitter tweet ID if successful"
    )
    username: str = Field(..., description="Twitter username that posted the tweet")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Tweet posted successfully",
                "tweet_id": "1234567890123456789",
                "username": "applyfirst_app"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connection status")
    accounts: List[str] = Field(..., description="List of configured Twitter usernames")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "accounts": ["applyfirst_app", "backup_account"]
            }
        }


class RefreshSessionResponse(BaseModel):
    """Response model for session refresh endpoint."""

    success: bool = Field(..., description="Whether the session was refreshed successfully")
    message: str = Field(..., description="Status message")
    username: str = Field(..., description="Twitter username that was refreshed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Session refreshed successfully",
                "username": "applyfirst_app"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None,
        description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Authentication failed",
                "detail": "Invalid credentials for username: applyfirst_app"
            }
        }


class BrowserCookie(BaseModel):
    """Single cookie from browser export."""

    name: str = Field(..., description="Cookie name")
    value: str = Field(..., description="Cookie value")
    domain: Optional[str] = Field(default=None, description="Cookie domain")
    expirationDate: Optional[float] = Field(default=None, description="Expiration timestamp")
    httpOnly: Optional[bool] = Field(default=None)
    secure: Optional[bool] = Field(default=None)
    path: Optional[str] = Field(default=None)
    sameSite: Optional[str] = Field(default=None)
    hostOnly: Optional[bool] = Field(default=None)
    session: Optional[bool] = Field(default=None)
    storeId: Optional[str] = Field(default=None)


class UpdateCookiesRequest(BaseModel):
    """Request model for updating cookies from browser export format."""

    username: str = Field(..., description="Twitter username to update cookies for")
    cookies: List[BrowserCookie] = Field(..., description="List of cookies from browser export")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "applyfirst_app",
                "cookies": [
                    {
                        "name": "auth_token",
                        "value": "abc123...",
                        "domain": ".x.com",
                        "httpOnly": True,
                        "secure": True
                    },
                    {
                        "name": "ct0",
                        "value": "def456...",
                        "domain": ".x.com"
                    }
                ]
            }
        }
