import os
import logging
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('smart_kuku')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Task configuration
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_acks_on_failure_or_timeout = False

# Retry configuration
app.conf.task_default_retry_delay = 5 * 60  # 5 minutes
app.conf.task_max_retries = 3
app.conf.task_soft_time_limit = 3600  # 1 hour
app.conf.task_time_limit = 3900  # 1 hour 5 minutes

# Beat configuration
app.conf.beat_schedule = {
    # Run at 2 AM daily to check and update subscription statuses
    'check-subscription-status': {
        'task': 'subscriptions.tasks.check_subscription_status',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {
            'expires': 3600,  # 1 hour
            'retry': True,
        },
    },
    # Run at 10 AM daily to send payment reminders
    'send-payment-reminders': {
        'task': 'subscriptions.tasks.send_payment_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10 AM daily
        'options': {
            'expires': 3600,  # 1 hour
            'retry': True,
        },
    },
    # Run at 4 AM daily to process subscription renewals
    'process-subscription-renewals': {
        'task': 'subscriptions.tasks.process_subscription_renewals',
        'schedule': crontab(hour=4, minute=0),  # 4 AM daily
        'options': {
            'expires': 3600,  # 1 hour
            'retry': True,
        },
    },
    # Run hourly to process failed payments
    'retry-failed-payments': {
        'task': 'subscriptions.tasks.retry_failed_payments',
        'schedule': crontab(minute=0),  # Every hour
        'options': {
            'expires': 1800,  # 30 minutes
            'retry': True,
        },
    },
}

# Error handling for tasks
@app.task(bind=True, max_retries=3)
def debug_task(self):
    """Debug task for testing Celery"""
    try:
        logger.info(f'Request: {self.request!r}')
    except Exception as e:
        logger.error(f'Error in debug_task: {str(e)}')
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute

# Task error handler
@app.task(bind=True)
def log_error(self, task_id, exc, *args, **kwargs):
    """Log errors from failed tasks"""
    logger.error(f'Task {task_id} failed with error: {str(exc)}')
    
    # Notify admin of critical task failures
    if hasattr(settings, 'ADMIN_EMAIL'):
        from django.core.mail import send_mail
        send_mail(
            subject=f'Celery Task Failed: {task_id}',
            message=f'Task {task_id} failed with error: {str(exc)}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True
        )

# Task success handler
@app.task(bind=True)
def log_success(self, retval, task_id, *args, **kwargs):
    """Log successful task completion"""
    logger.info(f'Task {task_id} completed successfully with result: {retval}')
    return retval
