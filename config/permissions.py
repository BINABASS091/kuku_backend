from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow reads to everyone authenticated; writes only to admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Accept Django admin flags or explicit ADMINISTRATOR role if present
        return bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'role', '').upper() == 'ADMINISTRATOR')


class IsFarmerOrAdmin(BasePermission):
    """
    Permission class that allows access to farmers for their own data,
    and full access to admin users.
    """
    def has_permission(self, request, view):
        # Allow all authenticated users to access the view
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow admins to access any object
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # For farmers, check if they own the object
        if hasattr(request.user, 'farmer_profile'):
            # Check if the object is a subscription owned by the farmer
            if hasattr(obj, 'farmer'):
                return obj.farmer == request.user.farmer_profile
                
            # Check if the object is related to a subscription owned by the farmer
            if hasattr(obj, 'farmer_subscription'):
                return obj.farmer_subscription.farmer == request.user.farmer_profile
                
            # Check if the object is a payment for a subscription owned by the farmer
            if hasattr(obj, 'subscription'):
                return obj.subscription.farmer == request.user.farmer_profile
                
        return False


class IsSubscriptionOwner(BasePermission):
    """
    Permission class that ensures users can only access their own subscription resources.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Allow admins to perform any action
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # For other methods, check if the user is a farmer
        if not hasattr(request.user, 'farmer_profile'):
            return False
            
        # For create/update/delete, we'll check in has_object_permission
        return True
    
    def has_object_permission(self, request, view, obj):
        # Allow admins to perform any action
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check if the user is a farmer and owns the subscription
        if hasattr(request.user, 'farmer_profile'):
            # For subscription resources, check the associated subscription
            if hasattr(obj, 'farmer_subscription'):
                return obj.farmer_subscription.farmer == request.user.farmer_profile
                
            # For subscriptions, check direct ownership
            if hasattr(obj, 'farmer'):
                return obj.farmer == request.user.farmer_profile
                
            # For payments, check the associated subscription
            if hasattr(obj, 'subscription'):
                return obj.subscription.farmer == request.user.farmer_profile
                
        return False
