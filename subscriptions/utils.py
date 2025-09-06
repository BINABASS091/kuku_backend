from datetime import timedelta
from django.utils import timezone
from .models import FarmerSubscription, SubscriptionStatus, Resource

def get_subscription_utilization(subscription):
    """
    Get the resource utilization for a subscription
    Returns a dictionary with hardware and software utilization
    """
    resources = subscription.resources.filter(status=True).select_related('resource')
    
    hardware_count = resources.filter(resource__resource_type='HARDWARE').count()
    software_count = resources.filter(resource__resource_type__in=['SOFTWARE', 'PREDICTION', 'ANALYTICS']).count()
    
    return {
        'hardware': {
            'used': hardware_count,
            'limit': subscription.sub_type.max_hardware_nodes,
            'available': max(0, subscription.sub_type.max_hardware_nodes - hardware_count)
        },
        'software': {
            'used': software_count,
            'limit': subscription.sub_type.max_software_services,
            'available': max(0, subscription.sub_type.max_software_services - software_count)
        }
    }

def can_add_resource(subscription, resource):
    """Check if a resource can be added to a subscription"""
    if resource.is_basic:
        return True
        
    utilization = get_subscription_utilization(subscription)
    
    if resource.resource_type == 'HARDWARE':
        return utilization['hardware']['available'] > 0
    else:  # Software, Prediction, or Analytics
        return utilization['software']['available'] > 0

def get_upcoming_renewals(days_ahead=7):
    """Get subscriptions that will renew in the next X days"""
    today = timezone.now().date()
    target_date = today + timedelta(days=days_ahead)
    
    return FarmerSubscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__lte=target_date,
        end_date__gte=today,
        auto_renew=True
    )

def get_expiring_soon_subscriptions(days_before=7):
    """Get active subscriptions that will expire soon"""
    today = timezone.now().date()
    target_date = today + timedelta(days=days_before)
    
    return FarmerSubscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__lte=target_date,
        end_date__gte=today,
        auto_renew=False
    )

def get_expired_subscriptions():
    """Get subscriptions that have expired"""
    return FarmerSubscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        end_date__lt=timezone.now().date()
    )

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

def get_subscription_resources_breakdown(subscription):
    """Get a detailed breakdown of resources in a subscription"""
    resources = subscription.resources.filter(status=True).select_related('resource')
    
    breakdown = {
        'hardware': [],
        'software': [],
        'predictions': [],
        'analytics': []
    }
    
    for sub_resource in resources:
        resource = sub_resource.resource
        item = {
            'id': resource.id,
            'name': resource.name,
            'category': resource.get_category_display(),
            'is_basic': resource.is_basic,
            'allocated_at': sub_resource.allocated_at
        }
        
        if resource.resource_type == 'HARDWARE':
            breakdown['hardware'].append(item)
        elif resource.resource_type == 'SOFTWARE':
            breakdown['software'].append(item)
        elif resource.resource_type == 'PREDICTION':
            breakdown['predictions'].append(item)
        elif resource.resource_type == 'ANALYTICS':
            breakdown['analytics'].append(item)
    
    return breakdown
