"""
Test script to verify the Geonode proxy is working correctly.
"""
import httpx

# Your proxy configuration
PROXY_URL = "http://geonode_5EqUD6ds7J-type-residential:8c94794e-0311-470d-9c3c-b2d85d74e00c@proxy.geonode.io:9001"

def test_proxy_connection():
    """Test if proxy can connect to the internet."""
    print("=" * 60)
    print("Testing Proxy Connection...")
    print("=" * 60)

    try:
        # Test basic connectivity
        print("\n1. Testing basic proxy connectivity...")
        client = httpx.Client(proxy=PROXY_URL, timeout=30.0)

        response = client.get("http://httpbin.org/ip")
        print(f"✅ Proxy is working!")
        print(f"   Your IP via proxy: {response.json()['origin']}")

        # Test Twitter accessibility
        print("\n2. Testing Twitter accessibility through proxy...")
        response = client.get("https://x.com", follow_redirects=True)
        print(f"✅ Can reach Twitter! Status: {response.status_code}")

        # Get headers
        print("\n3. Testing what Twitter sees...")
        response = client.get("http://httpbin.org/headers")
        print(f"✅ Headers sent:")
        import json
        print(json.dumps(response.json(), indent=2))

        client.close()

    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        print("\nPossible issues:")
        print("  - Proxy credentials incorrect")
        print("  - Proxy server down")
        print("  - Network connectivity issue")

if __name__ == "__main__":
    test_proxy_connection()
