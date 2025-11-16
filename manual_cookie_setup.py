"""
Manual cookie setup - Use this if automated login keeps failing with 403.

This script helps you manually extract cookies from your browser and save them
to MongoDB, bypassing the problematic automated login.

Instructions:
1. Log into Twitter manually in your browser
2. Use browser dev tools (F12) to export cookies
3. Save cookies to a file called 'cookies.json'
4. Run this script to import them to MongoDB
"""
import json
from app.config import settings
from app.database import cookie_db

def import_cookies_from_file(username: str, cookie_file: str = "cookies.json"):
    """
    Import cookies from a JSON file into MongoDB.

    Args:
        username: Twitter username
        cookie_file: Path to JSON file containing cookies
    """
    print("=" * 60)
    print("Manual Cookie Import")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Cookie file: {cookie_file}")
    print()

    try:
        # Read cookies from file
        with open(cookie_file, 'r') as f:
            data = json.load(f)

        # Handle different cookie formats
        # Format 1: Direct dict {name: value}
        if isinstance(data, dict) and 'auth_token' in data:
            cookies = data
        # Format 2: Array of cookie objects [{name, value, domain, ...}]
        elif isinstance(data, list):
            cookies = {cookie.get('name', ''): cookie.get('value', '') for cookie in data if 'name' in cookie}
        # Format 3: Nested format from some extensions
        elif isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
            # Extract cookie objects
            cookies = {}
            for key, val in data.items():
                if isinstance(val, dict) and 'value' in val:
                    cookies[key] = val['value']
                else:
                    cookies[key] = val
        else:
            cookies = data

        print(f"✅ Loaded {len(cookies)} cookies from file")

        # Check for critical cookies
        critical_cookies = ['auth_token', 'ct0']
        missing = [c for c in critical_cookies if c not in cookies]
        if missing:
            print(f"⚠️  Warning: Missing critical cookies: {missing}")
            print("   The session might not work without these!")

        # Connect to MongoDB
        cookie_db.connect()
        print("✅ Connected to MongoDB")

        # Save cookies
        cookie_db.save_cookies(username, cookies)
        print(f"✅ Cookies saved to MongoDB for user: {username}")

        # Verify
        loaded_cookies = cookie_db.load_cookies(username)
        if loaded_cookies:
            print(f"✅ Verified: {len(loaded_cookies)} cookies stored")
            print("\n🎉 Success! Your service should now work without login issues.")
            print("   Restart your service to use these cookies.")
        else:
            print("❌ Verification failed - cookies not found in database")

        cookie_db.disconnect()

    except FileNotFoundError:
        print(f"❌ File not found: {cookie_file}")
        print("\nHow to export cookies:")
        print("1. Open Twitter in browser and log in")
        print("2. Press F12 to open Developer Tools")
        print("3. Go to Application > Storage > Cookies > https://x.com")
        print("4. Copy all cookies")
        print("5. Use a browser extension like 'EditThisCookie' to export as JSON")
        print("6. Save as 'cookies.json' in this directory")

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    USERNAME = "applyfirst_app"

    print("\n📝 Instructions:")
    print("1. Manually log into https://x.com in your browser")
    print("2. Use browser extension to export cookies as JSON")
    print("3. Save the file as 'cookies.json' in this directory")
    print("4. Run this script again")
    print()

    import_cookies_from_file(USERNAME)
