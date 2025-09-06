from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import (
    SubscriptionType, Resource, FarmerSubscription, 
    FarmerSubscriptionResource, SubscriptionStatus, ResourceType
)

class SubscriptionService:
    """Service class for handling subscription-related business logic"""
    
    @staticmethod
    def create_subscription(farmer, subscription_type_id, duration_months=1, auto_renew=True):
        """Create a new subscription for a farmer"""
        try:
            subscription_type = SubscriptionType.objects.get(id=subscription_type_id)
        except SubscriptionType.DoesNotExist:
            raise ValidationError("Invalid subscription type")
        
        # Deactivate any existing active subscriptions
        FarmerSubscription.objects.filter(
            farmer=farmer,
            status=SubscriptionStatus.ACTIVE
        ).update(status=SubscriptionStatus.CANCELLED)
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        subscription = FarmerSubscription.objects.create(
            farmer=farmer,
            sub_type=subscription_type,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
            status=SubscriptionStatus.PENDING
        )
        
        # Add basic resources that come with the subscription
        basic_resources = Resource.objects.filter(is_basic=True)
        for resource in basic_resources:
            FarmerSubscriptionResource.objects.create(
                farmer_subscription=subscription,
                resource=resource,
                status=True
            )
            
        return subscription
    
    @staticmethod
    def add_resource_to_subscription(subscription_id, resource_id):
        """Add a resource to a subscription if allowed"""
        try:
            subscription = FarmerSubscription.objects.get(id=subscription_id)
            resource = Resource.objects.get(id=resource_id)
        except (FarmerSubscription.DoesNotExist, Resource.DoesNotExist):
            raise ValidationError("Invalid subscription or resource")
            
        if not subscription.is_active:
            raise ValidationError("Cannot add resources to an inactive subscription")
            
        if resource.is_basic:
            raise ValidationError("Basic resources are automatically added to all subscriptions")
            
        with transaction.atomic():
            # Check if already added
            if FarmerSubscriptionResource.objects.filter(
                farmer_subscription=subscription,
                resource=resource
            ).exists():
                raise ValidationError("Resource already added to this subscription")
                
            # Check subscription limits
            if not subscription.can_add_resource(resource):
                raise ValidationError(
                    "Cannot add more resources of this type. "
                    "Please upgrade your subscription or contact support."
                )
                
            # Add the resource
            FarmerSubscriptionResource.objects.create(
                farmer_subscription=subscription,
                resource=resource,
                status=True
            )
    
    @staticmethod
    def check_subscription_status():
        """Check and update subscription statuses (to be run as a scheduled task)"""
        today = timezone.now().date()
        
        # Expire old subscriptions
        FarmerSubscription.objects.filter(
            end_date__lt=today,
            status=SubscriptionStatus.ACTIVE
        ).update(status=SubscriptionStatus.EXPIRED)
        
        # Suspend subscriptions with pending payments
        pending_payment_subs = FarmerSubscription.objects.filter(
            status=SubscriptionStatus.PENDING,
            payments__status='PENDING',
            payments__due_date__lt=today - timedelta(days=7)  # 7 days grace period
        )
        pending_payment_subs.update(status=SubscriptionStatus.SUSPENDED)
    
    @staticmethod
    def get_available_resources(subscription):
        """Get all resources available to a subscription"""
        # Get all basic resources
        basic_resources = Resource.objects.filter(is_basic=True)
        
        # Get all resources included in the subscription
        subscribed_resources = Resource.objects.filter(
            allocations__farmer_subscription=subscription,
            allocations__status=True
        )
        
        # Combine and remove duplicates
        return (basic_resources | subscribed_resources).distinct()
    
    @staticmethod
    def get_subscription_utilization(subscription):
        """Get detailed resource utilization for a subscription"""
        return subscription.get_utilization()

    @staticmethod
    def upgrade_subscription(subscription, new_subscription_type_id):
        """Upgrade a subscription to a higher tier"""
        try:
            new_sub_type = SubscriptionType.objects.get(id=new_subscription_type_id)
        except SubscriptionType.DoesNotExist:
            raise ValidationError("Invalid subscription type")
            
        if new_sub_type.tier <= subscription.sub_type.tier:
            raise ValidationError("New subscription type must be of a higher tier")
            
        # Calculate prorated credit for remaining time
        remaining_days = (subscription.end_date - timezone.now().date()).days
        if remaining_days <= 0:
            remaining_days = 1
            
        daily_rate = subscription.sub_type.cost / 30  # Simple 30-day month
        credit = remaining_days * daily_rate
        
        # Create new subscription
        new_subscription = FarmerSubscription.objects.create(
            farmer=subscription.farmer,
            sub_type=new_sub_type,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),  # 1 month
            status=SubscriptionStatus.ACTIVE
        )
        
        # Transfer resources that are compatible with the new subscription
        resources = subscription.resources.filter(status=True).select_related('resource')
        for sub_resource in resources:
            if not sub_resource.resource.is_basic:
                try:
                    FarmerSubscriptionResource.objects.create(
                        farmer_subscription=new_subscription,
                        resource=sub_resource.resource,
                        status=True
                    )
                except:
                    # Skip if resource can't be added (e.g., not allowed in new tier)
                    continue
        
        # Mark old subscription as upgraded
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.notes = f"Upgraded to {new_sub_type.name}"
        subscription.save()
        
        return new_subscription
