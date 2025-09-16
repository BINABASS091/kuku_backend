from rest_framework import serializers
from .models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, Payment, ResourceType
)
from accounts.serializers import FarmerSerializer as AccountsFarmerSerializer
from accounts.models import Farmer
from .exceptions import (
    SubscriptionLimitExceeded, SubscriptionInactiveError
)
from .services import SubscriptionService
from .utils import get_subscription_utilization, get_available_resources


class SubscriptionTypeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='subscriptionTypeID', read_only=True)
    active_subscriptions_count = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    average_usage = serializers.SerializerMethodField()
    tier_display = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionType
        fields = [
            'id', 'subscriptionTypeID', 'name', 'tier', 'tier_display', 'farm_size', 'cost',
            'max_hardware_nodes', 'max_software_services',
            'includes_predictions', 'includes_analytics', 'description',
            'active_subscriptions_count', 'total_revenue', 'average_usage'
        ]
        read_only_fields = ['id', 'subscriptionTypeID']
    
    def get_active_subscriptions_count(self, obj):
        """Get number of active subscriptions for this type"""
        return obj.farmer_subscriptions.filter(status='ACTIVE').count()
    
    def get_total_revenue(self, obj):
        """Get total revenue from this subscription type"""
        from django.db.models import Sum
        from decimal import Decimal
        payments = obj.farmer_subscriptions.filter(
            status='ACTIVE'
        ).aggregate(total=Sum('subscription_typeID__cost'))
        return float(payments['total'] or Decimal('0.00'))
    
    def get_average_usage(self, obj):
        """Get average resource usage for this subscription type"""
        # This is a placeholder - would need actual usage tracking
        subscriptions = obj.farmer_subscriptions.filter(status='ACTIVE')
        if not subscriptions.exists():
            return 0
        # For now, return a mock percentage
        return 75.5
    
    def get_tier_display(self, obj):
        """Get human readable tier"""
        return obj.get_tier_display()


class ResourceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='resourceID', read_only=True)
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    subscriptions_using_count = serializers.SerializerMethodField()
    total_allocations = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id', 'resourceID', 'name', 'resource_type', 'resource_type_display',
            'category', 'category_display', 'unit_cost', 'status', 'status_display',
            'is_basic', 'description', 'created_at', 'updated_at',
            'subscriptions_using_count', 'total_allocations'
        ]
        read_only_fields = ['id', 'resourceID', 'created_at', 'updated_at']
    
    def get_subscriptions_using_count(self, obj):
        """Get number of subscriptions using this resource"""
        return FarmerSubscriptionResource.objects.filter(
            resourceID=obj, 
            farmerSubscriptionID__status='ACTIVE'
        ).count()
    
    def get_total_allocations(self, obj):
        """Get total quantity allocated across all subscriptions"""
        from django.db.models import Sum
        result = obj.allocations.aggregate(total=Sum('quantity'))
        return result['total'] or 0
    
    def get_status_display(self, obj):
        """Get human readable status"""
        return "Available" if obj.status else "Unavailable"


class FarmerSubscriptionListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='farmerSubscriptionID', read_only=True)
    farmer = AccountsFarmerSerializer(source='farmerID', read_only=True)
    subscription_type = SubscriptionTypeSerializer(source='subscription_typeID', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FarmerSubscription
        fields = [
            'id', 'farmerSubscriptionID', 'farmer', 'subscription_type', 'start_date', 'end_date',
            'status', 'status_display', 'auto_renew', 'created_at'
        ]
        read_only_fields = fields


class FarmerSubscriptionDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='farmerSubscriptionID', read_only=True)
    subscription_type = SubscriptionTypeSerializer(source='subscription_typeID', read_only=True)
    farmer = AccountsFarmerSerializer(source='farmerID', read_only=True)
    resources = serializers.SerializerMethodField()
    utilization = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = FarmerSubscription
        fields = [
            'id', 'farmerSubscriptionID', 'farmer', 'subscription_type', 'start_date', 'end_date',
            'status', 'status_display', 'auto_renew', 'notes', 'resources',
            'utilization', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_resources(self, obj):
        qs = get_available_resources(obj)
        return ResourceSerializer(qs, many=True).data

    def get_utilization(self, obj):
        return get_subscription_utilization(obj)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Defensive coercion: sometimes a DateField value may appear as datetime in certain backends
        for field in ('start_date', 'end_date'):
            # Already handled by get_start_date / get_end_date but keep for defense
            if field not in data or data[field] is None:
                value = getattr(instance, field, None)
                if value is not None and hasattr(value, 'year'):
                    if hasattr(value, 'hour'):
                        try:
                            value = value.date()
                        except Exception:
                            pass
                    data[field] = value.isoformat() if hasattr(value, 'isoformat') else value
        return data

    def get_start_date(self, obj):  # pragma: no cover simple coercion
        val = getattr(obj, 'start_date', None)
        if val is None:
            return None
        if hasattr(val, 'hour'):
            try:
                val = val.date()
            except Exception:
                pass
        return val.isoformat() if hasattr(val, 'isoformat') else val

    def get_end_date(self, obj):  # pragma: no cover simple coercion
        val = getattr(obj, 'end_date', None)
        if val is None:
            return None
        if hasattr(val, 'hour'):
            try:
                val = val.date()
            except Exception:
                pass
        return val.isoformat() if hasattr(val, 'isoformat') else val


class FarmerSubscriptionCreateSerializer(serializers.ModelSerializer):
    subscription_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionType.objects.all(),
        source='subscription_typeID',
        write_only=True
    )
    farmer_id = serializers.PrimaryKeyRelatedField(
        queryset=Farmer.objects.all(),
        source='farmerID',
        write_only=True,
        required=False
    )
    duration_months = serializers.IntegerField(min_value=1, max_value=12, default=1, write_only=True)

    class Meta:
        model = FarmerSubscription
        fields = ['farmer_id', 'subscription_type_id', 'duration_months', 'auto_renew']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError('Request context is required')

        subscription_type = validated_data.pop('subscription_typeID')
        duration_months = validated_data.pop('duration_months', 1)
        farmer = validated_data.pop('farmerID', None)

        # If no farmer specified and user is a farmer, use current user's farmer profile
        if not farmer:
            if hasattr(request.user, 'farmer_profile'):
                farmer = request.user.farmer_profile
            else:
                raise serializers.ValidationError('User is not a farmer and no farmer specified')

        # For admin users, allow specifying farmer_id
        if farmer != getattr(request.user, 'farmer_profile', None):
            if not (request.user.is_staff or request.user.is_superuser):
                raise serializers.ValidationError('Only admins can create subscriptions for other farmers')

        subscription = SubscriptionService.create_subscription(
            farmer=farmer,
            subscription_type_id=subscription_type.subscriptionTypeID,
            duration_months=duration_months,
            auto_renew=validated_data.get('auto_renew', True)
        )
        return subscription


class FarmerSubscriptionResourceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='farmerSubscriptionResourceID', read_only=True)
    resource_details = ResourceSerializer(source='resourceID', read_only=True)

    class Meta:
        model = FarmerSubscriptionResource
        fields = [
            'id', 'farmerSubscriptionResourceID', 'resourceID', 'resource_details',
            'quantity', 'status', 'allocated_at'
        ]
        read_only_fields = ['id', 'farmerSubscriptionResourceID', 'allocated_at', 'status']

    def validate(self, attrs):
        subscription = self.context.get('subscription')
        resource = attrs.get('resourceID')

        if not subscription:
            raise serializers.ValidationError('Subscription is required')
        if not subscription.is_active:
            raise SubscriptionInactiveError()
        if not resource:
            raise serializers.ValidationError({'resourceID': 'Resource is required'})

        # Enforce subscription limits using model method
        if not subscription.can_add_resource(resource):
            if resource.resource_type == ResourceType.HARDWARE:
                limit = subscription.subscription_typeID.max_hardware_nodes if subscription.subscription_typeID else 0
            else:
                limit = subscription.subscription_typeID.max_software_services if subscription.subscription_typeID else 0
            raise SubscriptionLimitExceeded(
                detail=f'Maximum {limit} {resource.get_resource_type_display().lower()} resources allowed'
            )
        return attrs

    def create(self, validated_data):
        subscription = self.context.get('subscription')
        resource = validated_data.get('resourceID')
        quantity = validated_data.get('quantity', 1)
        try:
            return FarmerSubscriptionResource.objects.create(
                farmerSubscriptionID=subscription,
                resourceID=resource,
                quantity=quantity
            )
        except Exception as exc:
            raise serializers.ValidationError(str(exc))


class PaymentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='paymentID', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'paymentID', 'amount', 'payment_date', 'due_date',
            'status', 'status_display', 'transaction_id',
            'receipt', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'paymentID', 'payment_date', 'created_at', 'updated_at']


class SubscriptionUpgradeSerializer(serializers.Serializer):
    new_subscription_type_id = serializers.PrimaryKeyRelatedField(queryset=SubscriptionType.objects.all())

    def validate(self, attrs):
        subscription = self.context.get('subscription')
        new_sub_type = attrs.get('new_subscription_type_id')
        if not subscription:
            raise serializers.ValidationError('Subscription is required')
        if new_sub_type.tier <= subscription.subscription_typeID.tier:
            raise serializers.ValidationError('New subscription must be of a higher tier')
        return attrs

    def create(self, validated_data):
        subscription = self.context.get('subscription')
        new_sub_type = validated_data.get('new_subscription_type_id')
        return SubscriptionService.upgrade_subscription(subscription, new_sub_type.subscriptionTypeID)
