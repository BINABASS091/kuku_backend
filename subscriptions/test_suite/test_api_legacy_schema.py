from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User, Farmer
from subscriptions.models import SubscriptionType, Resource, FarmerSubscription, SubscriptionStatus


class LegacySubscriptionAPITest(TestCase):
    """Smoke tests validating legacy field exposure & core flows."""

    def setUp(self):
        self.client = APIClient()

    def authenticate(self, username, password):
        token_resp = self.client.post('/api/v1/token/', {'username': username, 'password': password}, format='json')
        self.assertEqual(token_resp.status_code, 200)
        access = token_resp.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def test_create_subscription_and_upgrade(self):
        user = User.objects.create_user(username='farmer1', password='pass12345')
        farmer = Farmer.objects.create(user=user, full_name='Farmer One', address='Addr', email='f1@example.com', phone='123')
        st_basic = SubscriptionType.objects.create(name='Basic', tier='INDIVIDUAL', farm_size='Small')
        st_premium = SubscriptionType.objects.create(name='Premium', tier='PREMIUM', farm_size='Large')
        Resource.objects.create(name='Basic HW', resource_type='HARDWARE', category='INVENTORY', is_basic=True)

        self.authenticate('farmer1', 'pass12345')
        resp = self.client.post(reverse('farmer-subscription-list'), {
            'subscription_type_id': st_basic.subscriptionTypeID,
            'duration_months': 1,
            'auto_renew': True
        }, format='json')
        self.assertIn(resp.status_code, (200, 201))
        sub_id = resp.json()['farmerSubscriptionID']

        upgrade_url = reverse('farmer-subscription-upgrade', args=[sub_id])
        resp2 = self.client.post(upgrade_url, {
            'new_subscription_type_id': st_premium.subscriptionTypeID
        }, format='json')
        if resp2.status_code != 200:  # Debug aid
            try:
                print('DEBUG upgrade response:', resp2.status_code, resp2.json())
            except Exception:
                print('DEBUG upgrade raw content:', resp2.status_code, resp2.content)
        self.assertEqual(resp2.status_code, 200)

        self.assertGreaterEqual(
            FarmerSubscription.objects.filter(farmerID=farmer, status=SubscriptionStatus.CANCELLED).count(), 1
        )
        self.assertEqual(
            FarmerSubscription.objects.filter(farmerID=farmer, status=SubscriptionStatus.ACTIVE).count(), 1
        )

    def test_resource_limit_enforced(self):
        # Arrange
        user = User.objects.create_user(username='farmer2', password='pass12345')
        farmer = Farmer.objects.create(user=user, full_name='Farmer Two', address='Addr', email='f2@example.com', phone='456')
        st = SubscriptionType.objects.create(
            name='HWOnly', tier='INDIVIDUAL', farm_size='Small',
            max_hardware_nodes=1, max_software_services=0
        )
        r1 = Resource.objects.create(name='Node1', resource_type='HARDWARE', category='INVENTORY')
        r2 = Resource.objects.create(name='Node2', resource_type='HARDWARE', category='INVENTORY')

        # Create subscription
        self.authenticate('farmer2', 'pass12345')
        create_resp = self.client.post(reverse('farmer-subscription-list'), {
            'subscription_type_id': st.subscriptionTypeID,
            'duration_months': 1,
            'auto_renew': True
        }, format='json')
        self.assertIn(create_resp.status_code, (200, 201))
        sub = FarmerSubscription.objects.get(farmerID=farmer, status=SubscriptionStatus.ACTIVE)

        # Add first hardware node (allowed)
        add_url = reverse('subscription-resource-list', kwargs={'subscription_farmerSubscriptionID': sub.farmerSubscriptionID})
        resp1 = self.client.post(add_url, {'resourceID': r1.resourceID, 'quantity': 1}, format='json')
        self.assertIn(resp1.status_code, (200, 201))

        # Add second hardware node (should fail - exceeds max_hardware_nodes=1)
        resp2 = self.client.post(add_url, {'resourceID': r2.resourceID, 'quantity': 1}, format='json')
        self.assertEqual(resp2.status_code, 400)
