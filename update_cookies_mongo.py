#!/usr/bin/env python3
"""
Utility script to update Twitter cookies directly in MongoDB.

This script transforms browser-exported cookies into the format expected by twikit
and updates them in MongoDB without requiring a backend restart.

Usage:
    python update_cookies_mongo.py <username>

Then paste your cookies JSON when prompted.
"""

import json
import sys
from datetime import datetime
from pymongo import MongoClient
from app.config import settings


def transform_cookies(browser_cookies: list) -> dict:
    """
    Transform browser-exported cookies to twikit format.

    Args:
        browser_cookies: List of cookie objects from browser export

    Returns:
        Dictionary with {name: value} format for twikit
    """
    twikit_cookies = {}

    for cookie in browser_cookies:
        name = cookie.get("name")
        value = cookie.get("value")

        if name and value:
            twikit_cookies[name] = value

    return twikit_cookies


def update_cookies_in_mongo(username: str, cookies: dict) -> bool:
    """
    Update cookies for a Twitter account in MongoDB.

    Args:
        username: Twitter username
        cookies: Cookie dictionary in twikit format

    Returns:
        True if successful, False otherwise
    """
    try:
        # Connect to MongoDB
        mongo_uri = settings.get_mongo_uri()
        client = MongoClient(mongo_uri)
        db = client[settings.mongo_db]
        sessions_collection = db["twitter_sessions"]

        # Update or insert cookies
        session_data = {
            "username": username,
            "cookies": cookies,
            "updated_at": datetime.utcnow()
        }

        result = sessions_collection.update_one(
            {"username": username},
            {"$set": session_data},
            upsert=True
        )

        client.close()

        if result.modified_count > 0 or result.upserted_id:
            return True
        return True  # upsert with no changes still succeeds

    except Exception as e:
        print(f"Error updating MongoDB: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_cookies_mongo.py <username>")
        print("Example: python update_cookies_mongo.py applyfirst_app")
        sys.exit(1)

    username = sys.argv[1]

    print(f"Updating cookies for Twitter account: {username}")
    print("-" * 50)
    print("Paste your cookies JSON (from browser export), then press Enter twice:")
    print()

    # Read multi-line JSON input
    lines = []
    empty_line_count = 0

    while True:
        try:
            line = input()
            if line == "":
                empty_line_count += 1
                if empty_line_count >= 1 and lines:
                    break
            else:
                empty_line_count = 0
                lines.append(line)
        except EOFError:
            break

    if not lines:
        print("Error: No input provided")
        sys.exit(1)

    # Parse JSON
    json_str = "\n".join(lines)

    try:
        browser_cookies = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

    # Transform cookies
    twikit_cookies = transform_cookies(browser_cookies)

    print(f"\nTransformed {len(twikit_cookies)} cookies:")
    for name in twikit_cookies.keys():
        print(f"  - {name}")

    # Update MongoDB
    print(f"\nUpdating MongoDB for user '{username}'...")

    if update_cookies_in_mongo(username, twikit_cookies):
        print("\n✅ Cookies updated successfully!")
        print("\nThe backend will use these new cookies for the next tweet.")
        print("No restart required - cookies are loaded fresh from MongoDB for each operation.")
    else:
        print("\n❌ Failed to update cookies")
        sys.exit(1)


if __name__ == "__main__":
    main()
