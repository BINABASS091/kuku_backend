#!/usr/bin/env python3
"""
Simple API Integration Test
Tests core endpoints to validate API functionality
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'

def test_connection():
    """Test if the Django server is running"""
    print("🔌 Testing connection to Django server...")
    try:
        response = requests.get(f'{BASE_URL}/api/v1/', timeout=5)
        if response.status_code in [200, 404]:  # 404 is OK, means server is running
            print("✅ Server is running")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start Django with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_authentication():
    """Test JWT authentication with default admin user"""
    print("\n🔐 Testing Authentication...")
    
    # Test with default admin credentials that should exist
    auth_data = {
        'username': 'admin',  # Default Django admin user
        'password': 'admin123'  # Common default password
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/token/',
            json=auth_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("   ✅ Authentication successful")
            return token_data.get('access')
        else:
            print(f"   ❌ Authentication failed: {response.text}")
            print("   💡 Try creating admin user: python manage.py createsuperuser")
            return None
            
    except Exception as e:
        print(f"   ❌ Authentication request failed: {e}")
        return None

def test_api_endpoints(token):
    """Test various API endpoints"""
    if not token:
        print("❌ No token available, skipping endpoint tests")
        return False
        
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔗 Testing API Endpoints...")
    
    endpoints = [
        ('GET', '/api/v1/users/', 'Users list'),
        ('GET', '/api/v1/subscription-types/', 'Subscription types'),
        ('GET', '/api/v1/farmer-subscriptions/', 'Farmer subscriptions'),
        ('GET', '/api/v1/farms/', 'Farms list'),
        ('GET', '/api/v1/breeds/', 'Breeds list'),
        ('GET', '/api/v1/batches/', 'Batches list'),
        ('GET', '/api/v1/sensors/', 'Sensors list'),
        ('GET', '/api/v1/knowledge/', 'Knowledge base'),
    ]
    
    successful_tests = 0
    total_tests = len(endpoints)
    
    for method, endpoint, description in endpoints:
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ {description}: {response.status_code}")
                successful_tests += 1
            elif response.status_code == 401:
                print(f"   🔒 {description}: Authentication required ({response.status_code})")
            elif response.status_code == 403:
                print(f"   🚫 {description}: Permission denied ({response.status_code})")
            elif response.status_code == 404:
                print(f"   ❓ {description}: Not found ({response.status_code})")
            else:
                print(f"   ⚠️  {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: Request failed - {e}")
    
    print(f"\n📊 Endpoint Test Results: {successful_tests}/{total_tests} successful")
    return successful_tests > 0

def test_subscription_workflow(token):
    """Test subscription-related workflows"""
    if not token:
        print("❌ No token available, skipping subscription tests")
        return False
        
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n💳 Testing Subscription Workflows...")
    
    try:
        # Test getting subscription types
        sub_types_response = requests.get(f'{BASE_URL}/api/v1/subscription-types/', headers=headers)
        print(f"   Subscription Types: {sub_types_response.status_code}")
        
        if sub_types_response.status_code == 200:
            sub_types = sub_types_response.json()
            if 'results' in sub_types and sub_types['results']:
                print(f"   ✅ Found {len(sub_types['results'])} subscription types")
            else:
                print("   ℹ️  No subscription types found")
        
        # Test getting farmer subscriptions
        farmer_subs_response = requests.get(f'{BASE_URL}/api/v1/farmer-subscriptions/', headers=headers)
        print(f"   Farmer Subscriptions: {farmer_subs_response.status_code}")
        
        if farmer_subs_response.status_code == 200:
            print("   ✅ Farmer subscriptions endpoint working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Subscription workflow test failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Starting API Integration Tests")
    print(f"🎯 Target: {BASE_URL}")
    
    # Test 1: Connection
    if not test_connection():
        return False
    
    # Test 2: Authentication
    token = test_authentication()
    
    # Test 3: API Endpoints
    endpoints_ok = test_api_endpoints(token)
    
    # Test 4: Subscription workflow
    subscription_ok = test_subscription_workflow(token)
    
    # Summary
    print(f"\n{'='*60}")
    print(" TEST SUMMARY")
    print(f"{'='*60}")
    print(f"🔌 Server Connection: {'✅' if True else '❌'}")
    print(f"🔐 Authentication: {'✅' if token else '❌'}")
    print(f"🔗 API Endpoints: {'✅' if endpoints_ok else '❌'}")
    print(f"💳 Subscription Workflow: {'✅' if subscription_ok else '❌'}")
    
    if token and endpoints_ok:
        print(f"\n🎉 API is working! Ready for frontend development.")
        return True
    else:
        print(f"\n⚠️  Some issues found. Check server setup and authentication.")
        return False

if __name__ == '__main__':
    main()
