"""
Test Twitter login without proxy to isolate authentication issues.
"""
import asyncio
from twikit import Client

USERNAME = "applyfirst_app"
EMAIL = "mmazurovskiy@gmail.com"
PASSWORD = "2c}TFRcseEw+"

async def test_login_no_proxy():
    """Test login without proxy."""
    print("=" * 60)
    print("Testing Twitter Login WITHOUT Proxy")
    print("=" * 60)
    print(f"Username: {USERNAME}")
    print()

    try:
        # Create client without proxy
        client = Client('en-US')
        print("✅ Client created")

        print("\n🔐 Attempting login...")
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )

        print("✅ Login successful!")

        # Try to get user info to verify
        print("\n📋 Getting account info...")
        user = await client.user_by_screen_name(USERNAME)
        print(f"✅ Logged in as: {user.name} (@{user.screen_name})")
        print(f"   Followers: {user.followers_count}")

        # Save cookies for later use
        cookies = client.get_cookies()
        print(f"\n💾 Cookies saved: {len(cookies)} cookies")

        return True

    except Exception as e:
        print(f"❌ Login failed: {e}")
        print(f"\nError type: {type(e).__name__}")

        if "403" in str(e):
            print("\n⚠️  403 Forbidden - Possible causes:")
            print("   1. Account locked or suspended")
            print("   2. Twitter detecting automation")
            print("   3. Account needs email/phone verification")
            print("   4. Too many login attempts")
            print("\n💡 Solutions:")
            print("   - Log in manually on browser first")
            print("   - Complete any security verifications")
            print("   - Wait 15-30 minutes before retrying")
            print("   - Check if account is in good standing")

        return False

if __name__ == "__main__":
    asyncio.run(test_login_no_proxy())
