"""
Factories for creating test instances of subscription models.
"""
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, ResourceType, SubscriptionStatus
)
from farms.tests.factories import FarmerFactory


class SubscriptionTypeFactory(DjangoModelFactory):
    """Factory for creating SubscriptionType instances."""
    class Meta:
        model = SubscriptionType
        django_get_or_create = ('name',)
    
    name = factory.Sequence(lambda n: f'Subscription Type {n}')
    description = factory.Faker('sentence')
    tier = factory.Sequence(lambda n: n + 1)
    cost = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    max_hardware_nodes = 1
    max_software_services = 5
    max_prediction_requests = 100
    max_analytics_reports = 10
    is_active = True


class ResourceFactory(DjangoModelFactory):
    """Factory for creating Resource instances."""
    class Meta:
        model = Resource
        django_get_or_create = ('name',)
    
    name = factory.Sequence(lambda n: f'Resource {n}')
    description = factory.Faker('sentence')
    resource_type = factory.Iterator([rt[0] for rt in ResourceType.choices])
    category = factory.Faker('word')
    is_basic = False
    status = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class FarmerSubscriptionFactory(DjangoModelFactory):
    """Factory for creating FarmerSubscription instances."""
    class Meta:
        model = FarmerSubscription
    
    farmer = factory.SubFactory(FarmerFactory)
    sub_type = factory.SubFactory(SubscriptionTypeFactory)
    start_date = factory.LazyFunction(timezone.now().date)
    end_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    status = SubscriptionStatus.ACTIVE
    auto_renew = True
    notes = factory.Faker('sentence', nb_words=10)
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    
    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return
            
        if extracted:
            for resource in extracted:
                FarmerSubscriptionResourceFactory.create(
                    farmer_subscription=self,
                    resource=resource,
                    status=True
                )


class FarmerSubscriptionResourceFactory(DjangoModelFactory):
    """Factory for creating FarmerSubscriptionResource instances."""
    class Meta:
        model = FarmerSubscriptionResource
    
    farmer_subscription = factory.SubFactory(FarmerSubscriptionFactory)
    resource = factory.SubFactory(ResourceFactory)
    status = True
    allocated_at = factory.LazyFunction(timezone.now)
    deallocated_at = None
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class PaymentFactory(DjangoModelFactory):
    """Factory for creating Payment instances."""
    class Meta:
        model = 'subscriptions.Payment'
    
    subscription = factory.SubFactory(FarmerSubscriptionFactory)
    amount = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    currency = 'KES'
    payment_method = 'CARD'
    transaction_id = factory.Sequence(lambda n: f'tx_{n:010d}')
    status = 'COMPLETED'
    payment_date = factory.LazyFunction(timezone.now)
    receipt_number = factory.Sequence(lambda n: f'RCPT-{n:06d}')
    notes = factory.Faker('sentence')
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
