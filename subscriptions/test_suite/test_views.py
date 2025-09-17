"""Clean subscription and resource API tests."""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, Farmer
from subscriptions.models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, SubscriptionStatus
)


class SubscriptionViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.farmer = Farmer.objects.create(
            user=self.user, farmerName='Test User', address='Addr', email='t@example.com', phone='+111'
        )
        self.basic = SubscriptionType.objects.create(
            name='Basic', tier='INDIVIDUAL', farm_size='Small', max_hardware_nodes=1, max_software_services=2
        )
        self.premium = SubscriptionType.objects.create(
            name='Premium', tier='PREMIUM', farm_size='Large', max_hardware_nodes=5, max_software_services=10
        )
        self.hw = Resource.objects.create(name='HW1', resource_type='HARDWARE', category='INVENTORY', is_basic=True)
        self.sw = Resource.objects.create(name='SW1', resource_type='SOFTWARE', category='INVENTORY', is_basic=False)
        self.subscription = FarmerSubscription.objects.create(
            farmerID=self.farmer,
            subscription_typeID=self.basic,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        FarmerSubscriptionResource.objects.create(
            farmerSubscriptionID=self.subscription,
            resourceID=self.hw,
            status=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_subscription_status(self):
        url = reverse('subscription-status')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['has_active_subscription'])
        self.assertEqual(
            resp.data['subscription']['farmerSubscriptionID'],
            self.subscription.farmerSubscriptionID
        )

    def test_get_subscription_resources(self):
        url = reverse('farmer-subscription-resources', kwargs={'farmerSubscriptionID': self.subscription.farmerSubscriptionID})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)  # At least 1 resource (could be more if basic resources are auto-attached)

    def test_upgrade_subscription(self):
        url = reverse('farmer-subscription-upgrade', kwargs={'farmerSubscriptionID': self.subscription.farmerSubscriptionID})
        payload = {'new_subscription_type_id': self.premium.subscriptionTypeID}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['subscription_type']['subscriptionTypeID'], self.premium.subscriptionTypeID)


class ResourceViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ruser', password='pass12345')
        self.farmer = Farmer.objects.create(
            user=self.user, farmerName='Res User', address='Addr', email='r@example.com', phone='+222'
        )
        self.hw = Resource.objects.create(name='RHW', resource_type='HARDWARE', category='INVENTORY', is_basic=True)
        self.sw = Resource.objects.create(name='RSW', resource_type='SOFTWARE', category='INVENTORY', is_basic=False)
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_resources(self):
        url = reverse('resource-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_my_resources(self):
        url = reverse('resource-my-resources')  # verify actual route name later; fallback to manual path if needed
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertTrue(resp.data[0]['is_basic'])
