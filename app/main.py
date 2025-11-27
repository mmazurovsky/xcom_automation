"""
FastAPI application for Twitter automation using Twikit.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.auth import verify_api_key
from app.database import cookie_db
from app.twitter_service import twitter_service
from app.models import (
    TweetRequest,
    TweetResponse,
    HealthResponse,
    RefreshSessionResponse,
    ErrorResponse,
    UpdateCookiesRequest
)

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Twitter automation service...")

    try:
        # Connect to MongoDB
        cookie_db.connect()

        # Initialize Twitter accounts
        await twitter_service.initialize_accounts()

        logger.info("Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Twitter automation service...")
    cookie_db.disconnect()
    logger.info("Service shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Twitter Automation API",
    description="Automated tweet posting using Twikit library",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Twitter Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check the health status of the service.
    Returns service status, database connection, and configured accounts.
    """
    try:
        # Check if database is connected
        db_status = "connected" if cookie_db.client else "disconnected"

        # Get initialized accounts
        accounts = twitter_service.get_initialized_accounts()

        return HealthResponse(
            status="healthy",
            database=db_status,
            accounts=accounts
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@app.post(
    "/tweet",
    response_model=TweetResponse,
    tags=["Twitter"],
    summary="Post a tweet",
    dependencies=[Depends(verify_api_key)]
)
async def post_tweet(request: TweetRequest):
    """
    Post a tweet on behalf of the specified account.

    Requires API key authentication via X-API-Key header.

    Args:
        request: Tweet request containing username, text, and optional media_ids

    Returns:
        TweetResponse with success status and tweet ID
    """
    try:
        logger.info(f"Received tweet request for account: {request.username}")

        # Post tweet
        tweet_id = await twitter_service.post_tweet(
            username=request.username,
            text=request.text,
            media_ids=request.media_ids
        )

        return TweetResponse(
            success=True,
            message="Tweet posted successfully",
            tweet_id=tweet_id,
            username=request.username
        )

    except ValueError as e:
        logger.error(f"Invalid account: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post tweet: {str(e)}"
        )


@app.post(
    "/refresh-session/{username}",
    response_model=RefreshSessionResponse,
    tags=["Twitter"],
    summary="Refresh account session",
    dependencies=[Depends(verify_api_key)]
)
async def refresh_session(username: str):
    """
    Force re-authentication for a specific Twitter account.
    This will delete the existing session and create a new one.

    Requires API key authentication via X-API-Key header.

    Args:
        username: Twitter username to refresh

    Returns:
        RefreshSessionResponse with success status
    """
    try:
        logger.info(f"Refreshing session for account: {username}")

        success = await twitter_service.refresh_session(username)

        if success:
            return RefreshSessionResponse(
                success=True,
                message="Session refreshed successfully",
                username=username
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh session for account: {username}"
            )

    except Exception as e:
        logger.error(f"Failed to refresh session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post(
    "/reload-cookies/{username}",
    response_model=RefreshSessionResponse,
    tags=["Twitter"],
    summary="Reload cookies from MongoDB",
    dependencies=[Depends(verify_api_key)]
)
async def reload_cookies(username: str):
    """
    Reload cookies from MongoDB into the in-memory client.
    Use this after manually updating cookies in MongoDB (e.g., via update_cookies_mongo.py).

    This does NOT re-authenticate - it just loads the existing cookies from the database.

    Requires API key authentication via X-API-Key header.

    Args:
        username: Twitter username to reload cookies for

    Returns:
        RefreshSessionResponse with success status
    """
    try:
        logger.info(f"Reloading cookies from database for account: {username}")

        success = twitter_service.reload_cookies_from_db(username)

        if success:
            return RefreshSessionResponse(
                success=True,
                message="Cookies reloaded from database successfully",
                username=username
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to reload cookies for account: {username}. Account may not be initialized or no cookies in database."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload cookies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post(
    "/update-cookies",
    response_model=RefreshSessionResponse,
    tags=["Twitter"],
    summary="Update cookies from browser export",
    dependencies=[Depends(verify_api_key)]
)
async def update_cookies(request: UpdateCookiesRequest):
    """
    Update cookies for a Twitter account using browser-exported cookie format.

    This endpoint:
    1. Transforms browser cookies to twikit format
    2. Saves them to MongoDB
    3. Reloads them into the running client

    No restart or redeployment required.

    Requires API key authentication via X-API-Key header.

    Args:
        request: Contains username and list of browser-exported cookies

    Returns:
        RefreshSessionResponse with success status
    """
    try:
        username = request.username
        logger.info(f"[COOKIE UPDATE] Starting cookie update for account: {username}")

        # Transform browser cookies to twikit format {name: value}
        twikit_cookies = {}
        for cookie in request.cookies:
            twikit_cookies[cookie.name] = cookie.value

        logger.info(f"[COOKIE UPDATE] Transformed {len(twikit_cookies)} cookies for {username}")

        # Save to MongoDB
        if not cookie_db.save_cookies(username, twikit_cookies):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save cookies to database for {username}"
            )

        logger.info(f"[COOKIE UPDATE] Saved {len(twikit_cookies)} cookies to database for {username}")

        # Reload into running client or initialize if not yet initialized
        is_existing_client = username in twitter_service.clients

        if is_existing_client:
            logger.info(f"[COOKIE UPDATE] Reloading cookies into existing client for {username}")
            if twitter_service.reload_cookies_from_db(username):
                logger.info(f"[COOKIE UPDATE] Successfully reloaded cookies for {username}")
                return RefreshSessionResponse(
                    success=True,
                    message=f"Cookies updated and reloaded successfully ({len(twikit_cookies)} cookies)",
                    username=username
                )
        else:
            logger.info(f"[COOKIE UPDATE] Account not yet initialized, creating new client for {username}")

        # Client not initialized or reload failed - initialize from the new cookies
        if await twitter_service.initialize_from_cookies(username):
            logger.info(f"[COOKIE UPDATE] Successfully initialized account {username} from new cookies")
            return RefreshSessionResponse(
                success=True,
                message=f"Cookies saved and account initialized successfully ({len(twikit_cookies)} cookies)",
                username=username
            )
        else:
            # Failed to initialize - this is a critical failure
            logger.error(f"[COOKIE UPDATE] FAILED to initialize account {username} from cookies")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cookies saved to database but failed to initialize client for {username}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cookies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get(
    "/cookie-health/{username}",
    tags=["Health"],
    summary="Check cookie health for an account"
)
async def check_cookie_health(username: str):
    """
    Check if cookies are still valid for a Twitter account.
    Returns cookie status and expiration warning.

    Args:
        username: Twitter username to check

    Returns:
        Cookie health status
    """
    try:
        client = twitter_service.get_client(username)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not initialized: {username}"
            )

        # Try to verify the session is still valid
        try:
            user = await client.user_by_screen_name(username)

            return {
                "username": username,
                "cookie_status": "healthy",
                "authenticated": True,
                "account_name": user.name,
                "message": "Cookies are valid and working"
            }

        except Exception as auth_error:
            # Cookies likely expired
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "username": username,
                    "cookie_status": "expired",
                    "authenticated": False,
                    "message": "Cookies have expired - please refresh",
                    "error": str(auth_error)
                }
            )

    except Exception as e:
        logger.error(f"Failed to check cookie health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level
    )
