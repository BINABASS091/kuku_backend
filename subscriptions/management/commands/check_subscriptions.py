import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from ...models import FarmerSubscription, SubscriptionStatus, Payment
from ...services import SubscriptionService

logger = logging.getLogger(__name__)

def send_subscription_email(subject, template_name, context, to_email):
    """Helper function to send subscription-related emails"""
    try:
        message = render_to_string(f'subscriptions/emails/{template_name}.txt', context)
        html_message = render_to_string(f'subscriptions/emails/{template_name}.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False

class Command(BaseCommand):
    help = 'Check and update subscription statuses, send notifications, and handle renewals'

    def handle(self, *args, **options):
        self.stdout.write('Starting subscription check...')
        
        # Check for expired subscriptions
        expired_count = self.check_expired_subscriptions()
        self.stdout.write(f'Marked {expired_count} subscriptions as expired')
        
        # Check for subscriptions that need renewal
        renewed_count = self.check_renewals()
        self.stdout.write(f'Processed {renewed_count} subscription renewals')
        
        # Check for subscriptions that need payment reminders
        reminded_count = self.send_payment_reminders()
        self.stdout.write(f'Sent {reminded_count} payment reminders')
        
        self.stdout.write('Subscription check completed successfully')
    
    def check_expired_subscriptions(self):
        """Mark expired subscriptions and notify users"""
        today = timezone.now().date()
        expired = FarmerSubscription.objects.filter(
            end_date__lt=today,
            status=SubscriptionStatus.ACTIVE
        ).select_related('farmer__user', 'sub_type')
        
        count = 0
        for subscription in expired:
            try:
                # Update status
                subscription.status = SubscriptionStatus.EXPIRED
                subscription.save(update_fields=['status', 'updated_at'])
                
                # Send expiration notification
                context = {
                    'farmer': subscription.farmer,
                    'subscription': subscription,
                    'expiration_date': subscription.end_date,
                    'renewal_url': f"{settings.FRONTEND_URL}/subscriptions/renew/{subscription.id}"
                }
                
                send_subscription_email(
                    subject=f"Your {subscription.sub_type.name} subscription has expired",
                    template_name='subscription_expired',
                    context=context,
                    to_email=subscription.farmer.user.email
                )
                
                count += 1
                self.stdout.write(f"Marked subscription {subscription.id} as expired and notified {subscription.farmer.user.email}")
                
            except Exception as e:
                logger.error(f"Error processing expired subscription {getattr(subscription, 'id', 'unknown')}: {str(e)}")
                self.stderr.write(f"Error processing subscription: {str(e)}")
                
        return count
    
    def check_renewals(self):
        """Handle automatic renewals"""
        today = timezone.now().date()
        renew_window_start = today - timezone.timedelta(days=3)  # 3 days before expiration
        
        # Get active subscriptions that are set to auto-renew and are about to expire
        to_renew = FarmerSubscription.objects.filter(
            auto_renew=True,
            status=SubscriptionStatus.ACTIVE,
            end_date__lte=today + timezone.timedelta(days=3),  # Due in 3 days or less
            end_date__gte=renew_window_start
        )
        
        renewed_count = 0
        for subscription in to_renew:
            try:
                # Process payment (implement your payment processing logic here)
                payment_successful = self.process_renewal_payment(subscription)
                
                if payment_successful:
                    # Extend the subscription
                    new_end_date = subscription.end_date + timezone.timedelta(days=30)  # 1 month extension
                    subscription.end_date = new_end_date
                    subscription.save()
                    renewed_count += 1
                    
                    # TODO: Send renewal confirmation
                else:
                    # TODO: Handle failed payment
                    pass
                    
            except Exception as e:
                self.stderr.write(f'Error renewing subscription {subscription.id}: {str(e)}')
                
        return renewed_count
    
    def process_renewal_payment(self, subscription):
        """Process payment for subscription renewal"""
        try:
            # In a real implementation, integrate with your payment gateway here
            # This is a simplified example that creates a payment record
            
            payment = Payment.objects.create(
                subscription=subscription,
                amount=subscription.sub_type.cost,
                currency='KES',
                payment_method='AUTOMATIC',
                status='COMPLETED',
                payment_date=timezone.now(),
                notes=f'Automatic renewal for {subscription.sub_type.name} subscription'
            )
            
            # Log the payment
            logger.info(f"Processed payment {payment.id} for subscription {subscription.id}")
            return True
            
        except Exception as e:
            logger.error(f"Payment processing failed for subscription {subscription.id}: {str(e)}")
            # Notify admin of payment failure
            if hasattr(settings, 'ADMIN_EMAIL'):
                send_mail(
                    subject=f'Payment Processing Error - Subscription {subscription.id}',
                    message=f'Failed to process payment for subscription {subscription.id}: {str(e)}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True
                )
            return False
    
    def send_payment_reminders(self):
        """Send payment reminders for upcoming or overdue payments"""
        today = timezone.now().date()
        reminder_date = today + timezone.timedelta(days=3)  # 3 days before due date
        
        # Get subscriptions with payments due soon
        subscriptions = FarmerSubscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            end_date=reminder_date,
            auto_renew=True
        ).select_related('farmer__user', 'sub_type')
        
        reminded_count = 0
        for subscription in subscriptions:
            try:
                # Prepare email context
                context = {
                    'farmer': subscription.farmer,
                    'subscription': subscription,
                    'renewal_date': subscription.end_date,
                    'amount': subscription.sub_type.cost,
                    'payment_url': f"{settings.FRONTEND_URL}/payments/renew/{subscription.id}"
                }
                
                # Send reminder email
                email_sent = send_subscription_email(
                    subject=f"Renewal Reminder: Your {subscription.sub_type.name} subscription",
                    template_name='renewal_reminder',
                    context=context,
                    to_email=subscription.farmer.user.email
                )
                
                if email_sent:
                    reminded_count += 1
                    self.stdout.write(f"Sent renewal reminder for subscription {subscription.id} to {subscription.farmer.user.email}")
                else:
                    self.stderr.write(f"Failed to send renewal reminder for subscription {subscription.id}")
                    
            except Exception as e:
                logger.error(f"Error sending payment reminder for subscription {subscription.id}: {str(e)}")
                self.stderr.write(f'Error sending payment reminder for subscription {subscription.id}: {str(e)}')
                
        return reminded_count
