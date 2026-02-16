"""
Test Registration Script
Run this to test if registration works
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# Test data
test_user = {
    "name": "Test User",
    "email": "test@example.com",
    "phone": "1234567890",
    "password": "password123"
}

print("🧪 Testing Registration...")
print(f"Sending request to {BASE_URL}/api/auth/register")
print(f"Data: {json.dumps(test_user, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=test_user,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("\n✅ SUCCESS! Registration worked!")
        print("You can now login with:")
        print(f"  Email: {test_user['email']}")
        print(f"  Password: {test_user['password']}")
    else:
        print("\n❌ FAILED! Check the error message above")
        
except requests.exceptions.ConnectionError:
    print("❌ Error: Cannot connect to the server")
    print("Make sure the app is running: python app.py")
except Exception as e:
    print(f"❌ Error: {str(e)}")
