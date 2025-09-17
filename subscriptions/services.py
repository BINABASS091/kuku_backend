from datetime import timedelta, datetime
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, SubscriptionStatus
)


class SubscriptionService:
    """Service class for handling subscription-related business logic."""

    @staticmethod
    def create_subscription(farmer, subscription_type_id, duration_months=1, auto_renew=True):
        try:
            subscription_type = SubscriptionType.objects.get(subscriptionTypeID=subscription_type_id)
        except SubscriptionType.DoesNotExist:
            raise ValidationError("Invalid subscription type")

        # Deactivate existing active subscriptions for farmer
        FarmerSubscription.objects.filter(
            farmerID=farmer, status=SubscriptionStatus.ACTIVE
        ).update(status=SubscriptionStatus.CANCELLED)

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30 * duration_months)

        subscription = FarmerSubscription.objects.create(
            farmerID=farmer,
            subscription_typeID=subscription_type,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
            status=SubscriptionStatus.ACTIVE
        )

        # Attach basic resources
        for resource in Resource.objects.filter(is_basic=True):
            FarmerSubscriptionResource.objects.create(
                farmerSubscriptionID=subscription,
                resourceID=resource,
                status=True
            )
        return subscription

    @staticmethod
    def add_resource_to_subscription(subscription_id, resource_id):
        try:
            subscription = FarmerSubscription.objects.get(farmerSubscriptionID=subscription_id)
            resource = Resource.objects.get(resourceID=resource_id)
        except (FarmerSubscription.DoesNotExist, Resource.DoesNotExist):
            raise ValidationError("Invalid subscription or resource")

        if not subscription.is_active:
            raise ValidationError("Cannot add resources to an inactive subscription")
        if resource.is_basic:
            raise ValidationError("Basic resources are automatically added to all subscriptions")

        with transaction.atomic():
            if FarmerSubscriptionResource.objects.filter(
                farmerSubscriptionID=subscription, resourceID=resource
            ).exists():
                raise ValidationError("Resource already added to this subscription")

            if not subscription.can_add_resource(resource):
                raise ValidationError(
                    "Cannot add more resources of this type. Please upgrade your subscription or contact support."
                )

            FarmerSubscriptionResource.objects.create(
                farmerSubscriptionID=subscription,
                resourceID=resource,
                status=True
            )

    @staticmethod
    def check_subscription_status():
        today = timezone.now().date()
        FarmerSubscription.objects.filter(
            end_date__lt=today, status=SubscriptionStatus.ACTIVE
        ).update(status=SubscriptionStatus.EXPIRED)

        pending_payment_subs = FarmerSubscription.objects.filter(
            status=SubscriptionStatus.PENDING,
            payments__status='PENDING',
            payments__due_date__lt=today - timedelta(days=7)
        )
        pending_payment_subs.update(status=SubscriptionStatus.SUSPENDED)

    @staticmethod
    def get_available_resources(subscription):
        basic_resources = Resource.objects.filter(is_basic=True)
        subscribed_resources = Resource.objects.filter(
            allocations__farmerSubscriptionID=subscription,
            allocations__status=True
        )
        return (basic_resources | subscribed_resources).distinct()

    @staticmethod
    def get_subscription_utilization(subscription):
        return subscription.get_utilization()


    @staticmethod
    def upgrade_subscription(subscription, new_subscription_type_id):
        if not subscription:
            raise ValidationError("Subscription context missing")

        try:
            new_sub_type = SubscriptionType.objects.get(subscriptionTypeID=new_subscription_type_id)
        except SubscriptionType.DoesNotExist:
            raise ValidationError("Invalid subscription type")

        tier_order = {'INDIVIDUAL': 0, 'NORMAL': 1, 'PREMIUM': 2}
        current_tier = subscription.subscription_typeID.tier if subscription.subscription_typeID else 'INDIVIDUAL'
        if tier_order.get(new_sub_type.tier, -1) <= tier_order.get(current_tier, -1):
            raise ValidationError("New subscription type must be of a higher tier")

        remaining_days = (subscription.end_date - timezone.now().date()).days if subscription.end_date else 0
        if remaining_days <= 0:
            remaining_days = 1
        daily_rate = (subscription.subscription_typeID.cost if subscription.subscription_typeID else 0) / 30
        _credit = remaining_days * daily_rate  # placeholder

        new_subscription = FarmerSubscription.objects.create(
            farmerID=subscription.farmerID,
            subscription_typeID=new_sub_type,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE
        )

        for sub_resource in subscription.subscription_resources.filter(status=True).select_related('resourceID'):
            res = sub_resource.resourceID
            if res.is_basic:
                continue
            try:
                FarmerSubscriptionResource.objects.create(
                    farmerSubscriptionID=new_subscription,
                    resourceID=res,
                    status=True
                )
            except Exception:
                continue

        FarmerSubscription.objects.filter(pk=subscription.pk).update(
            status=SubscriptionStatus.CANCELLED,
            notes=f"Upgraded to {new_sub_type.name}"
        )

        changed = False
        for attr in ('start_date', 'end_date'):
            val = getattr(new_subscription, attr, None)
            if isinstance(val, datetime):
                setattr(new_subscription, attr, val.date())
                changed = True
        if changed:
            new_subscription.save(update_fields=['start_date', 'end_date'])

        return new_subscription
