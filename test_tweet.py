"""
Test script to post a tweet with a link using the Twitter automation API.
"""
import requests
import json

# Configuration
API_KEY = "LF@$Xba5aM63!m2zSdr&"
BASE_URL = "http://localhost:8000"
USERNAME = "applyfirst_app"

def test_health():
    """Test the health endpoint."""
    print("=" * 60)
    print("Testing Health Endpoint...")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"✅ Database: {data['database']}")
        print(f"✅ Accounts: {', '.join(data['accounts'])}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(f"   Response: {response.text}")

    print()

def post_tweet_with_link():
    """Post a tweet with a google.com link."""
    print("=" * 60)
    print("Posting Tweet with Link...")
    print("=" * 60)

    tweet_data = {
        "username": USERNAME,
        "text": "Check out this amazing search engine! https://google.com"
    }

    print(f"Username: {tweet_data['username']}")
    print(f"Text: {tweet_data['text']}")
    print()

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/tweet",
        headers=headers,
        json=tweet_data
    )

    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("✅ Tweet Posted Successfully!")
        print(f"   Success: {data['success']}")
        print(f"   Message: {data['message']}")
        print(f"   Tweet ID: {data['tweet_id']}")
        print(f"   Username: {data['username']}")
        print(f"\n   View tweet at: https://twitter.com/{data['username']}/status/{data['tweet_id']}")
    else:
        print("❌ Tweet Posting Failed!")
        try:
            error_data = response.json()
            print(f"   Error: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Response: {response.text}")

    print()

if __name__ == "__main__":
    print("\n🐦 Twitter Automation Service Test")
    print("=" * 60)
    print()

    # Test health first
    test_health()

    # Post tweet with link
    post_tweet_with_link()

    print("=" * 60)
    print("Test completed!")
    print("=" * 60)
