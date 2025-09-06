from rest_framework.exceptions import APIException
from rest_framework import status

class SubscriptionError(APIException):
    """Base exception for subscription-related errors"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A subscription error occurred'
    default_code = 'subscription_error'

class SubscriptionLimitExceeded(SubscriptionError):
    """Raised when a subscription limit is exceeded"""
    default_detail = 'Subscription limit exceeded for this resource type'
    default_code = 'subscription_limit_exceeded'

class SubscriptionInactiveError(SubscriptionError):
    """Raised when trying to perform an action on an inactive subscription"""
    default_detail = 'This subscription is not active'
    default_code = 'subscription_inactive'

class ResourceNotAvailableError(SubscriptionError):
    """Raised when a requested resource is not available"""
    default_detail = 'The requested resource is not available'
    default_code = 'resource_not_available'

class PaymentRequiredError(SubscriptionError):
    """Raised when a payment is required"""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Payment is required to access this resource'
    default_code = 'payment_required'

class UpgradeRequiredError(SubscriptionError):
    """Raised when a subscription upgrade is required"""
    status_code = status.HTTP_426_UPGRADE_REQUIRED
    default_detail = 'A subscription upgrade is required for this action'
    default_code = 'upgrade_required'
