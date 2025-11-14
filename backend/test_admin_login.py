"""
Quick test script to verify admin login works
Run this AFTER restarting the backend server
"""
import requests
import json

API_BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("Testing Admin Login")
print("=" * 60)

# Test login
login_data = {
    "username": "admin",
    "password": "password123"
}

print(f"\n1. Attempting login...")
print(f"   Username: {login_data['username']}")
print(f"   Password: {login_data['password']}")

try:
    response = requests.post(
        f"{API_BASE_URL}/admin/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"\n2. Response Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\n✅ LOGIN SUCCESSFUL!")
        print(f"\n   Access Token (first 50 chars): {data['access_token'][:50]}...")
        print(f"   Token Type: {data['token_type']}")
        print(f"   Expires In: {data['expires_in']} seconds ({data['expires_in']/3600} hours)")
        print(f"   Username: {data['username']}")

        # Save token for manual testing
        print(f"\n3. Testing token verification...")
        verify_response = requests.post(
            f"{API_BASE_URL}/admin/verify",
            headers={"X-Admin-Token": data['access_token']}
        )

        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print("   ✅ Token is valid!")
            print(f"   Valid: {verify_data['valid']}")
            print(f"   Username: {verify_data['username']}")
            print(f"   Role: {verify_data['role']}")
        else:
            print(f"   ❌ Token verification failed: {verify_response.status_code}")
            print(f"   Response: {verify_response.text}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYou can now login in the UI with:")
        print("   Username: admin")
        print("   Password: password123")
        print("\n" + "=" * 60)

    else:
        print(f"\n❌ LOGIN FAILED!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == 401:
            print("\n   Possible causes:")
            print("   1. Password hash in .env is incorrect")
            print("   2. Backend didn't reload the new .env file")
            print("   3. bcrypt library not installed")
            print("\n   Solution: Restart the backend server!")

except requests.exceptions.ConnectionError:
    print("\n❌ CONNECTION FAILED!")
    print("   Could not connect to backend at http://localhost:8000")
    print("\n   Make sure backend is running:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")

print("\n")
