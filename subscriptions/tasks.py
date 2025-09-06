import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .models import FarmerSubscription, SubscriptionStatus, Payment
from .utils import get_expiring_soon_subscriptions, get_expired_subscriptions

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

@shared_task
def check_subscription_status():
    """Check and update subscription statuses"""
    logger.info("Running subscription status check...")
    
    # Get expired subscriptions and mark them as expired
    expired = get_expired_subscriptions()
    expired_count = 0
    
    for subscription in expired.select_related('farmer__user', 'sub_type'):
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
            
            expired_count += 1
            logger.info(f"Marked subscription {subscription.id} as expired and notified {subscription.farmer.user.email}")
            
        except Exception as e:
            logger.error(f"Error processing expired subscription {getattr(subscription, 'id', 'unknown')}: {str(e)}")
    
    logger.info(f"Processed {expired_count} expired subscriptions")
    return {"expired_count": expired_count}

@shared_task
def send_payment_reminders():
    """Send payment reminders for subscriptions due soon"""
    logger.info("Sending payment reminders...")
    
    # Get subscriptions expiring in 3 days
    due_soon = get_expiring_soon_subscriptions(days_before=3).select_related('farmer__user', 'sub_type')
    
    reminder_count = 0
    for subscription in due_soon:
        try:
            context = {
                'farmer': subscription.farmer,
                'subscription': subscription,
                'renewal_date': subscription.end_date,
                'amount': subscription.sub_type.cost,
                'payment_url': f"{settings.FRONTEND_URL}/payments/renew/{subscription.id}"
            }
            
            if subscription.auto_renew:
                # For auto-renewing subscriptions, send a reminder about the upcoming renewal
                email_sent = send_subscription_email(
                    subject=f"Renewal Reminder: Your {subscription.sub_type.name} subscription",
                    template_name='renewal_reminder',
                    context=context,
                    to_email=subscription.farmer.user.email
                )
            else:
                # For non-auto-renewing subscriptions, send a payment reminder
                email_sent = send_subscription_email(
                    subject=f"Action Required: Renew your {subscription.sub_type.name} subscription",
                    template_name='payment_reminder',
                    context=context,
                    to_email=subscription.farmer.user.email
                )
                
            if email_sent:
                reminder_count += 1
                logger.info(f"Sent reminder for subscription {subscription.id} to {subscription.farmer.user.email}")
            else:
                logger.error(f"Failed to send reminder for subscription {subscription.id}")
                
        except Exception as e:
            logger.error(f"Error sending reminder for subscription {getattr(subscription, 'id', 'unknown')}: {str(e)}")
    
    logger.info(f"Sent {reminder_count} payment/renewal reminders")
    return {"reminder_count": reminder_count}

@shared_task
def process_subscription_renewals():
    """Process automatic subscription renewals"""
    logger.info("Processing subscription renewals...")
    
    today = timezone.now().date()
    renew_window_start = today - timedelta(days=3)
    
    # Get active subscriptions that are set to auto-renew and are about to expire
    to_renew = FarmerSubscription.objects.filter(
        auto_renew=True,
        status=SubscriptionStatus.ACTIVE,
        end_date__lte=today + timedelta(days=3),  # Due in 3 days or less
        end_date__gte=renew_window_start
    ).select_related('farmer__user', 'sub_type')
    
    renewed_count = 0
    for subscription in to_renew:
        try:
            # Process payment
            payment_successful = process_payment.delay(
                subscription_id=subscription.id,
                amount=float(subscription.sub_type.cost),
                description=f"Renewal for {subscription.sub_type.name} subscription"
            ).get()
            
            if payment_successful:
                # Extend the subscription
                new_end_date = subscription.end_date + timedelta(days=30)  # 1 month extension
                subscription.end_date = new_end_date
                subscription.save(update_fields=['end_date', 'updated_at'])
                
                # Send renewal confirmation
                send_subscription_email(
                    subject=f"Renewal Confirmation: Your {subscription.sub_type.name} subscription",
                    template_name='renewal_confirmation',
                    context={
                        'farmer': subscription.farmer,
                        'subscription': subscription,
                        'new_end_date': new_end_date,
                        'receipt_url': f"{settings.FRONTEND_URL}/payments/receipt/{subscription.latest_payment().id}"
                    },
                    to_email=subscription.farmer.user.email
                )
                
                renewed_count += 1
                logger.info(f"Renewed subscription {subscription.id} until {new_end_date}")
            else:
                logger.error(f"Payment failed for subscription {subscription.id}")
                
                # Notify admin of payment failure
                if hasattr(settings, 'ADMIN_EMAIL'):
                    send_mail(
                        subject=f'Payment Failed - Subscription {subscription.id}',
                        message=f'Failed to process payment for subscription {subscription.id} (Farmer: {subscription.farmer.user.email})',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL],
                        fail_silently=True
                    )
                
        except Exception as e:
            logger.error(f"Error renewing subscription {getattr(subscription, 'id', 'unknown')}: {str(e)}")
    
    logger.info(f"Processed {renewed_count} subscription renewals")
    return {"renewed_count": renewed_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)  # 5 minutes
retry_failed_payments = None  # This will be defined below after the process_payment function

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_payment(self, subscription_id, amount, description, is_retry=False):
    """
    Process a payment for a subscription
    
    Args:
        subscription_id: ID of the subscription to process payment for
        amount: Amount to charge
        description: Description of the payment
        is_retry: Whether this is a retry attempt (default: False)
    """
    try:
        subscription = FarmerSubscription.objects.select_related('farmer__user', 'sub_type').get(id=subscription_id)
        
        # In a real implementation, integrate with your payment gateway here
        # This is a simplified example that creates a payment record
        payment = Payment.objects.create(
            subscription=subscription,
            amount=amount,
            currency='KES',
            payment_method='AUTOMATIC',
            status='PENDING',  # Start with pending status
            payment_date=timezone.now(),
            description=description,
            notes='Payment processing started' + (' (retry attempt)' if is_retry else '')
        )
        
        # Simulate payment processing
        # In a real implementation, this would call your payment gateway
        logger.info(f"Processing payment {payment.id} for subscription {subscription.id}")
        
        # Simulate a small chance of failure for testing
        if not is_retry and random.random() < 0.1:  # 10% chance of failure on first attempt
            raise Exception("Payment gateway temporarily unavailable")
        
        # Update payment status to completed
        payment.status = 'COMPLETED'
        payment.payment_date = timezone.now()
        payment.notes = 'Payment processed successfully'
        payment.save()
        
        logger.info(f"Successfully processed payment {payment.id} for subscription {subscription.id}")
        return True
        
    except Exception as exc:
        logger.error(f"Payment processing failed for subscription {subscription_id}: {str(exc)}")
        
        # Update payment status if it was created
        if 'payment' in locals():
            payment.status = 'FAILED'
            payment.notes = f'Payment failed: {str(exc)}'
            payment.save()
            
            # Notify user of payment failure
            send_subscription_reminder.delay(
                subscription_id=subscription_id,
                reminder_type='payment_failed',
                error_message=str(exc),
                retry_available=True
            )
        
        # Retry the task if we have retries left
        try:
            self.retry(exc=exc, countdown=self.default_retry_delay * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for payment on subscription {subscription_id}")
            
            # Notify admin of critical failure
            if hasattr(settings, 'ADMIN_EMAIL'):
                send_mail(
                    subject=f'Critical: Payment Processing Failed - Subscription {subscription_id}',
                    message=f'Failed to process payment after {self.max_retries} retries.\n\n'
                            f'Subscription ID: {subscription_id}\n'
                            f'Amount: {amount} KES\n'
                            f'Error: {str(exc)}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True
                )
        
        return False

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
retry_failed_payments = None  # This will be defined after the function

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def retry_failed_payments(self):
    """
    Task to retry failed payments for subscriptions
    """
    try:
        # Find failed payments from the last 7 days that haven't been retried too many times
        cutoff_date = timezone.now() - timedelta(days=7)
        
        failed_payments = Payment.objects.filter(
            status='FAILED',
            created_at__gte=cutoff_date,
            retry_count__lt=3  # Maximum number of retries
        ).select_related('subscription')
        
        retry_count = 0
        success_count = 0
        
        for payment in failed_payments:
            try:
                # Skip if subscription is no longer active
                if payment.subscription.status != SubscriptionStatus.ACTIVE:
                    continue
                    
                # Skip if payment is too old
                if (timezone.now() - payment.created_at).days > 7:
                    continue
                
                # Update retry count
                payment.retry_count = (payment.retry_count or 0) + 1
                payment.last_retry = timezone.now()
                payment.notes = f"Retry attempt {payment.retry_count} of 3"
                payment.save()
                
                # Retry the payment
                success = process_payment.delay(
                    subscription_id=payment.subscription.id,
                    amount=float(payment.amount),
                    description=f"Retry: {payment.description}",
                    is_retry=True
                ).get()
                
                if success:
                    success_count += 1
                    
                    # Update subscription if this was a renewal payment
                    if 'renewal' in payment.description.lower():
                        subscription = payment.subscription
                        subscription.end_date = subscription.end_date + timedelta(days=30)  # Extend by 1 month
                        subscription.save(update_fields=['end_date', 'updated_at'])
                        
                        # Send renewal confirmation
                        send_subscription_reminder.delay(
                            subscription_id=subscription.id,
                            reminder_type='renewal_confirmation',
                            new_end_date=subscription.end_date
                        )
                
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Error retrying payment {payment.id}: {str(e)}")
                continue
        
        logger.info(f"Retried {retry_count} failed payments, {success_count} were successful")
        return {"retried": retry_count, "successful": success_count}
        
    except Exception as e:
        logger.error(f"Error in retry_failed_payments task: {str(e)}")
        try:
            self.retry(exc=e, countdown=self.default_retry_delay * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for retry_failed_payments task")
        return {"error": str(e), "retried": 0, "successful": 0}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_reminder(self, subscription_id, reminder_type, **kwargs):
    """
    Send a subscription-related email notification using templates
    
    Args:
        subscription_id: ID of the subscription
        reminder_type: Type of reminder (e.g., 'payment_reminder', 'renewal_confirmation')
        **kwargs: Additional context data for the email template
    """
    try:
        subscription = FarmerSubscription.objects.select_related('farmer__user', 'sub_type').get(id=subscription_id)
        farmer = subscription.farmer
        user = farmer.user
        
        # Default context for all email templates
        context = {
            'farmer': farmer,
            'subscription': subscription,
            'renewal_date': subscription.end_date,
            'amount': subscription.sub_type.cost,
            'payment_url': f"{settings.FRONTEND_URL}/payments/renew/{subscription.id}",
            **kwargs  # Allow additional context to be passed
        }
        
        email_config = {
            'payment_reminder': {
                'subject': f"Action Required: Renew your {subscription.sub_type.name} subscription",
                'template': 'payment_reminder'
            },
            'renewal_reminder': {
                'subject': f"Renewal Reminder: Your {subscription.sub_type.name} subscription",
                'template': 'renewal_reminder'
            },
            'renewal_confirmation': {
                'subject': f"Renewal Confirmation: Your {subscription.sub_type.name} subscription",
                'template': 'renewal_confirmation'
            },
            'subscription_expired': {
                'subject': f"Your {subscription.sub_type.name} subscription has expired",
                'template': 'subscription_expired'
            },
            'payment_failed': {
                'subject': f"Payment Issue: Your {subscription.sub_type.name} subscription",
                'template': 'payment_failed'
            }
        }
        
        config = email_config.get(reminder_type)
        if not config:
            logger.error(f"Unknown reminder type: {reminder_type}")
            return {"status": "error", "error": f"Unknown reminder type: {reminder_type}", "email_sent": False}
        
        # Send the email using our template
        email_sent = send_subscription_email(
            subject=config['subject'],
            template_name=config['template'],
            context=context,
            to_email=user.email
        )
        
        if email_sent:
            logger.info(f"Sent {reminder_type} email to {user.email}")
            return {"status": "success", "email_sent": True}
        else:
            logger.error(f"Failed to send {reminder_type} email to {user.email}")
            return {"status": "error", "error": "Email sending failed", "email_sent": False}
            
    except FarmerSubscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found")
        return {"status": "error", "error": "Subscription not found", "email_sent": False}
        
    except Exception as e:
        logger.error(f"Error sending {reminder_type} email for subscription {subscription_id}: {str(e)}")
        return {"status": "error", "error": str(e), "email_sent": False}
