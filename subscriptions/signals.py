from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import FarmerSubscription, SubscriptionStatus
from .services import SubscriptionService

@receiver(post_save, sender=FarmerSubscription)
def handle_subscription_save(sender, instance, created, **kwargs):
    """Handle subscription save events"""
    if created:
        # New subscription created
        pass
    else:
        # Subscription updated
        pass

@receiver(pre_save, sender=FarmerSubscription)
def handle_subscription_status_change(sender, instance, **kwargs):
    """Handle subscription status changes"""
    if not instance.pk:
        return  # New instance, no previous state
        
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            # Status changed
            if instance.status == SubscriptionStatus.ACTIVE:
                # Subscription activated
                instance.activation_date = timezone.now().date()
                # Send welcome email or notification
                pass
                
    except sender.DoesNotExist:
        pass  # New instance

@receiver(post_save, sender=FarmerSubscription)
def handle_subscription_activation(sender, instance, created, **kwargs):
    """Handle subscription activation"""
    if not created and instance.status == SubscriptionStatus.ACTIVE:
        # Check if this is a reactivation
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.status != SubscriptionStatus.ACTIVE:
                # Subscription was just activated
                pass  # Add any activation logic here
        except sender.DoesNotExist:
            pass
