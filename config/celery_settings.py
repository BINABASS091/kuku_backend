# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'
CELERY_ENABLE_UTC = True

# Email settings for notifications
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development
DEFAULT_FROM_EMAIL = 'noreply@smartkuku.com'

# Task settings
CELERY_TASK_ALWAYS_EAGER = False  # Set to True for testing to run tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions in eager mode

# Task time limits (in seconds)
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Process one task at a time
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Restart worker after 100 tasks

# Beat settings (for scheduled tasks)
CELERY_BEAT_SCHEDULE = {
    'check-subscription-status': {
        'task': 'subscriptions.tasks.check_subscription_status',
        'schedule': 86400.0,  # Run daily
    },
    'send-payment-reminders': {
        'task': 'subscriptions.tasks.send_payment_reminders',
        'schedule': 86400.0,  # Run daily
    },
    'process-subscription-renewals': {
        'task': 'subscriptions.tasks.process_subscription_renewals',
        'schedule': 86400.0,  # Run daily
    },
}
