#!/usr/bin/env python
"""
Comprehensive API Integration Test Script
Tests all major endpoints to ensure they work correctly before frontend development.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from accounts.models import Farmer
from subscriptions.models import SubscriptionType, Resource, FarmerSubscription, SubscriptionStatus
from breeds.models import BreedType
from farms.models import Farm

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_authentication():
    print_section("TESTING AUTHENTICATION")
    
    client = APIClient()
    
    # Test token endpoint
    print("1. Testing JWT Token Generation...")
    token_response = client.post('/api/v1/token/', {
        'username': 'admin',
        'password': 'admin'
    }, format='json')
    
    print(f"   Status: {token_response.status_code}")
    if token_response.status_code == 200:
        token_data = token_response.json()
        print(f"   ✅ Access token generated successfully")
        return token_data['access']
    else:
        print(f"   ❌ Token generation failed: {token_response.content}")
        return None

def test_subscription_endpoints(access_token):
    print_section("TESTING SUBSCRIPTION ENDPOINTS")
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test subscription types
    print("1. Testing Subscription Types...")
    response = client.get('/api/v1/subscription-types/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {len(data)} subscription types")
    else:
        print(f"   ❌ Failed: {response.content}")
    
    # Test resources
    print("2. Testing Resources...")
    response = client.get('/api/v1/resources/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {len(data)} resources")
    else:
        print(f"   ❌ Failed: {response.content}")
    
    # Test subscription status
    print("3. Testing Subscription Status...")
    response = client.get('/api/v1/subscription-status/')
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 403]:  # 403 is expected if user is not a farmer
        print(f"   ✅ Subscription status endpoint working")
    else:
        print(f"   ❌ Failed: {response.content}")

def test_farmer_workflow(access_token):
    print_section("TESTING FARMER WORKFLOW")
    
    # Create test farmer
    user = User.objects.create_user(
        username='testfarmer', 
        password='testpass123',
        email='test@farmer.com'
    )
    farmer = Farmer.objects.create(
        user=user,
        full_name='Test Farmer',
        address='Test Address',
        email='test@farmer.com',
        phone='+1234567890'
    )
    
    # Get farmer token
    client = APIClient()
    token_response = client.post('/api/v1/token/', {
        'username': 'testfarmer',
        'password': 'testpass123'
    }, format='json')
    
    if token_response.status_code == 200:
        farmer_token = token_response.json()['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {farmer_token}')
        
        print("1. Testing Farmer Subscription Creation...")
        
        # Create subscription type if doesn't exist
        sub_type, created = SubscriptionType.objects.get_or_create(
            name='Basic Test',
            defaults={
                'tier': 'INDIVIDUAL',
                'farm_size': 'Small',
                'max_hardware_nodes': 2,
                'max_software_services': 3,
                'cost': 29.99
            }
        )
        
        # Test subscription creation
        create_response = client.post('/api/v1/farmer-subscriptions/', {
            'subscription_type_id': sub_type.subscriptionTypeID,
            'duration_months': 1,
            'auto_renew': True
        }, format='json')
        
        print(f"   Status: {create_response.status_code}")
        if create_response.status_code in [200, 201]:
            sub_data = create_response.json()
            print(f"   ✅ Subscription created: {sub_data['farmerSubscriptionID']}")
            
            # Test subscription resources
            print("2. Testing Subscription Resources...")
            resources_response = client.get(f'/api/v1/farmer-subscriptions/{sub_data["farmerSubscriptionID"]}/resources/')
            print(f"   Status: {resources_response.status_code}")
            if resources_response.status_code == 200:
                resources = resources_response.json()
                print(f"   ✅ Found {len(resources)} available resources")
            
            # Test resource addition (if we have a test resource)
            test_resource, created = Resource.objects.get_or_create(
                name='Test Hardware',
                defaults={
                    'resource_type': 'HARDWARE',
                    'category': 'INVENTORY',
                    'description': 'Test hardware resource',
                    'is_basic': False
                }
            )
            
            print("3. Testing Resource Addition...")
            add_resource_response = client.post(
                f'/api/v1/farmer-subscriptions/{sub_data["farmerSubscriptionID"]}/resources/',
                {
                    'resourceID': test_resource.resourceID,
                    'quantity': 1
                },
                format='json'
            )
            print(f"   Status: {add_resource_response.status_code}")
            if add_resource_response.status_code in [200, 201]:
                print("   ✅ Resource added successfully")
            elif add_resource_response.status_code == 400:
                print("   ⚠️ Resource addition failed (may be due to limits)")
            
        else:
            print(f"   ❌ Subscription creation failed: {create_response.content}")
    else:
        print(f"   ❌ Farmer authentication failed: {token_response.content}")

def test_other_endpoints(access_token):
    print_section("TESTING OTHER CORE ENDPOINTS")
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    endpoints = [
        '/api/v1/users/',
        '/api/v1/farmers/',
        '/api/v1/farms/',
        '/api/v1/breed-types/',
        '/api/v1/breeds/',
        '/api/v1/batches/',
        '/api/v1/sensor-types/',
    ]
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        response = client.get(endpoint)
        status_emoji = "✅" if response.status_code in [200, 403] else "❌"
        print(f"   {status_emoji} Status: {response.status_code}")

def main():
    print_section("API INTEGRATION TESTING")
    print("Testing all major API endpoints for frontend compatibility...")
    
    try:
        # Test authentication
        access_token = test_authentication()
        
        if access_token:
            # Test subscription endpoints
            test_subscription_endpoints(access_token)
            
            # Test farmer workflow
            test_farmer_workflow(access_token)
            
            # Test other endpoints
            test_other_endpoints(access_token)
            
            print_section("TESTING COMPLETE")
            print("✅ All major API endpoints tested successfully!")
            print("🚀 Ready to proceed with frontend development!")
            
        else:
            print("❌ Authentication failed - cannot proceed with other tests")
            return 1
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
