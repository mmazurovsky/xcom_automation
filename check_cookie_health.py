"""
Check Twitter cookie health and expiration status.
Run this periodically to monitor when cookies need refreshing.
"""
import asyncio
from datetime import datetime
from app.database import cookie_db
from app.config import settings
from twikit import Client

async def check_cookie_health(username: str):
    """
    Test if cookies are still valid for a given account.

    Args:
        username: Twitter username to check
    """
    print("=" * 60)
    print(f"Cookie Health Check - {username}")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Connect to MongoDB
        cookie_db.connect()
        print("✅ Connected to MongoDB")

        # Load cookies
        cookies = cookie_db.load_cookies(username)

        if not cookies:
            print(f"❌ No cookies found for {username}")
            print("   Action required: Export fresh cookies")
            return False

        print(f"✅ Found {len(cookies)} cookies in database")

        # Check critical cookies exist
        critical_cookies = ['auth_token', 'ct0']
        missing = [c for c in critical_cookies if c not in cookies]

        if missing:
            print(f"⚠️  Missing critical cookies: {missing}")
            print("   Action required: Export fresh cookies")
            return False

        print(f"✅ All critical cookies present")

        # Test cookies by making an API call
        print("\n🔍 Testing cookies with Twitter API...")

        proxy_url = settings.get_proxy_url()
        if proxy_url:
            client = Client('en-US', proxy=proxy_url)
            print(f"✅ Using proxy: {settings.proxy_server}")
        else:
            client = Client('en-US')
            print("⚠️  No proxy configured")

        # Load cookies into client
        client.set_cookies(cookies)

        # Try to get user info (this will fail if cookies expired)
        user = await client.user_by_screen_name(username)

        print(f"✅ Cookies are valid!")
        print(f"\n📊 Account Status:")
        print(f"   Name: {user.name}")
        print(f"   Username: @{user.screen_name}")
        print(f"   Followers: {user.followers_count}")
        print(f"   Following: {user.following_count}")

        print(f"\n💚 Cookie Health: HEALTHY")
        print(f"   No action needed - cookies working perfectly")

        cookie_db.disconnect()
        return True

    except Exception as e:
        print(f"\n❌ Cookie Health: EXPIRED or INVALID")
        print(f"   Error: {e}")

        if "401" in str(e) or "auth" in str(e).lower():
            print(f"\n⚠️  AUTHENTICATION FAILED")
            print(f"   Your cookies have expired!")
            print(f"\n📋 Action Required:")
            print(f"   1. Go to https://x.com and log in as {username}")
            print(f"   2. Export cookies using Cookie-Editor extension")
            print(f"   3. Save as cookies.json")
            print(f"   4. Run: python manual_cookie_setup.py")
            print(f"   5. Restart your service")

        cookie_db.disconnect()
        return False

async def check_all_accounts():
    """Check cookie health for all configured accounts."""
    accounts = settings.get_twitter_accounts()

    print("\n🔍 Checking all configured accounts...")
    print()

    results = {}
    for account in accounts:
        is_healthy = await check_cookie_health(account.username)
        results[account.username] = is_healthy
        print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)

    for username, is_healthy in results.items():
        status = "✅ HEALTHY" if is_healthy else "❌ NEEDS REFRESH"
        print(f"{username}: {status}")

    print()

    if all(results.values()):
        print("🎉 All accounts are healthy!")
    else:
        print("⚠️  Some accounts need cookie refresh")

if __name__ == "__main__":
    # Check specific account
    USERNAME = "applyfirst_app"

    # Run check
    asyncio.run(check_cookie_health(USERNAME))

    # Or check all accounts:
    # asyncio.run(check_all_accounts())
