"""
Tests for subscription views.
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from farms.models import Farmer
from .factories import (
    SubscriptionTypeFactory, ResourceFactory,
    FarmerSubscriptionFactory, FarmerSubscriptionResourceFactory
)
from ..models import SubscriptionStatus, ResourceType

User = get_user_model()


class SubscriptionViewSetTestCase(APITestCase):
    """Test cases for SubscriptionViewSet."""

    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.farmer = Farmer.objects.create(
            user=self.user,
            phone_number='+254712345678',
            location='Nairobi, Kenya',
            farm_name='Test Farm'
        )
        
        # Create subscription types
        self.basic_sub = SubscriptionTypeFactory(
            name='Basic',
            tier=1,
            cost=0,
            max_hardware_nodes=1,
            max_software_services=2,
            description='Basic free tier'
        )
        
        self.premium_sub = SubscriptionTypeFactory(
            name='Premium',
            tier=2,
            cost=2999,
            max_hardware_nodes=5,
            max_software_services=10,
            description='Premium tier with more resources'
        )
        
        # Create resources
        self.hardware_resource = ResourceFactory(
            name='Raspberry Pi',
            resource_type=ResourceType.HARDWARE,
            is_basic=True
        )
        
        self.software_resource = ResourceFactory(
            name='Advanced Analytics',
            resource_type=ResourceType.SOFTWARE,
            is_basic=False
        )
        
        # Create a subscription for the test user
        self.subscription = FarmerSubscriptionFactory(
            farmer=self.farmer,
            sub_type=self.basic_sub,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # Add a resource to the subscription
        self.subscription_resource = FarmerSubscriptionResourceFactory(
            farmer_subscription=self.subscription,
            resource=self.hardware_resource,
            status=True
        )
        
        # Generate JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_subscription_status(self):
        ""Test getting the current user's subscription status.""
        url = reverse('subscription-status-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_active_subscription'])
        self.assertEqual(response.data['subscription']['id'], self.subscription.id)
    
    def test_get_subscription_resources(self):
        ""Test getting resources for a subscription.""
        url = reverse('farmer-subscriptions-resources', kwargs={'pk': self.subscription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should have the hardware resource
    
    def test_get_subscription_utilization(self):
        ""Test getting resource utilization for a subscription.""
        url = reverse('farmer-subscriptions-utilization', kwargs={'pk': self.subscription.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('hardware', response.data)
        self.assertIn('software', response.data)
    
    def test_upgrade_subscription(self):
        ""Test upgrading a subscription to a higher tier.""
        url = reverse('farmer-subscriptions-upgrade', kwargs={'pk': self.subscription.id})
        data = {
            'subscription_type': self.premium_sub.id,
            'payment_method': 'CARD',
            'auto_renew': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sub_type']['id'], self.premium_sub.id)
    
    def test_cancel_subscription(self):
        ""Test canceling a subscription.""
        url = reverse('farmer-subscriptions-cancel', kwargs={'pk': self.subscription.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh the subscription from the database
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.auto_renew)


class ResourceViewSetTestCase(APITestCase):
    """Test cases for ResourceViewSet."""
    
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.farmer = Farmer.objects.create(
            user=self.user,
            phone_number='+254712345678',
            location='Nairobi, Kenya',
            farm_name='Test Farm'
        )
        
        # Create resources
        self.hardware_resource = ResourceFactory(
            name='Raspberry Pi',
            resource_type=ResourceType.HARDWARE,
            is_basic=True
        )
        
        self.software_resource = ResourceFactory(
            name='Advanced Analytics',
            resource_type=ResourceType.SOFTWARE,
            is_basic=False
        )
        
        # Generate JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_resources(self):
        ""Test listing all resources.""
        url = reverse('resource-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both resources should be listed
    
    def test_get_my_resources(self):
        ""Test getting resources available to the current user.""
        url = reverse('resource-my')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return basic resources for users without an active subscription
        self.assertEqual(len(response.data), 1)  # Only the basic hardware resource
        self.assertTrue(response.data[0]['is_basic'])
