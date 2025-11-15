"""
API key authentication for FastAPI endpoints.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

# API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from request headers.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key
