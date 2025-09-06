from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, Payment, SubscriptionStatus,
    ResourceType, ResourceCategory
)
from accounts.serializers import FarmerSerializer as AccountsFarmerSerializer
from .exceptions import (
    SubscriptionLimitExceeded, SubscriptionInactiveError,
    ResourceNotAvailableError, PaymentRequiredError, UpgradeRequiredError
)
from .services import SubscriptionService
from .utils import get_subscription_utilization, get_available_resources

class ResourceTypeField(serializers.ChoiceField):
    def to_representation(self, value):
        return ResourceType(value).label

class ResourceCategoryField(serializers.ChoiceField):
    def to_representation(self, value):
        return ResourceCategory(value).label

class SubscriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionType
        fields = [
            'id', 'name', 'tier', 'farm_size', 'cost',
            'max_hardware_nodes', 'max_software_services',
            'includes_predictions', 'includes_analytics', 'description'
        ]
        read_only_fields = ['id']

class ResourceSerializer(serializers.ModelSerializer):
    resource_type_display = serializers.CharField(
        source='get_resource_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'resource_type', 'resource_type_display',
            'category', 'category_display', 'unit_cost', 'status',
            'is_basic', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class FarmerSubscriptionListSerializer(serializers.ModelSerializer):
    subscription_type = SubscriptionTypeSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = FarmerSubscription
        fields = [
            'id', 'subscription_type', 'start_date', 'end_date',
            'status', 'status_display', 'auto_renew', 'created_at'
        ]
        read_only_fields = fields

class FarmerSubscriptionDetailSerializer(serializers.ModelSerializer):
    subscription_type = SubscriptionTypeSerializer(read_only=True)
    farmer = AccountsFarmerSerializer(read_only=True)
    resources = serializers.SerializerMethodField()
    utilization = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = FarmerSubscription
        fields = [
            'id', 'farmer', 'subscription_type', 'start_date', 'end_date',
            'status', 'status_display', 'auto_renew', 'notes', 'resources',
            'utilization', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_resources(self, obj):
        from .serializers import ResourceSerializer
        resources = get_available_resources(obj)
        return ResourceSerializer(resources, many=True).data
    
    def get_utilization(self, obj):
        return get_subscription_utilization(obj)

class FarmerSubscriptionCreateSerializer(serializers.ModelSerializer):
    subscription_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionType.objects.all(),
        source='subscription_type',
        write_only=True
    )
    duration_months = serializers.IntegerField(
        min_value=1,
        max_value=12,
        default=1,
        write_only=True
    )
    
    class Meta:
        model = FarmerSubscription
        fields = ['subscription_type_id', 'duration_months', 'auto_renew']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'farmer_profile'):
            raise serializers.ValidationError("User is not a farmer")
        
        subscription_type = validated_data.pop('subscription_type')
        duration_months = validated_data.pop('duration_months', 1)
        
        subscription = SubscriptionService.create_subscription(
            farmer=request.user.farmer_profile,
            subscription_type_id=subscription_type.id,
            duration_months=duration_months,
            auto_renew=validated_data.get('auto_renew', True)
        )
        
        return subscription

class FarmerSubscriptionResourceSerializer(serializers.ModelSerializer):
    resource_details = ResourceSerializer(
        source='resource',
        read_only=True
    )
    
    class Meta:
        model = FarmerSubscriptionResource
        fields = ['id', 'resource', 'resource_details', 'quantity', 'status', 'allocated_at']
        read_only_fields = ['allocated_at', 'status']
    
    def validate(self, attrs):
        subscription = self.context.get('subscription')
        resource = attrs.get('resource')
        
        if not subscription:
            raise serializers.ValidationError("Subscription is required")
        
        if not subscription.is_active:
            raise SubscriptionInactiveError()
        
        # Check if resource can be added to subscription
        if not SubscriptionService.can_add_resource(subscription, resource):
            if resource.resource_type == ResourceType.HARDWARE:
                limit = subscription.sub_type.max_hardware_nodes
            else:
                limit = subscription.sub_type.max_software_services
                
            raise SubscriptionLimitExceeded(
                detail=f"Maximum {limit} {resource.get_resource_type_display().lower()} resources allowed"
            )
            
        return attrs
    
    def create(self, validated_data):
        subscription = self.context.get('subscription')
        resource = validated_data.get('resource')
        
        try:
            subscription_resource = FarmerSubscriptionResource.objects.create(
                farmer_subscription=subscription,
                resource=resource,
                quantity=validated_data.get('quantity', 1)
            )
            return subscription_resource
        except Exception as e:
            raise serializers.ValidationError(str(e))

class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'payment_date', 'due_date',
            'status', 'status_display', 'transaction_id',
            'receipt', 'notes', 'created_at'
        ]
        read_only_fields = ['payment_date', 'created_at', 'updated_at']

class SubscriptionUpgradeSerializer(serializers.Serializer):
    new_subscription_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionType.objects.all()
    )
    
    def validate(self, attrs):
        subscription = self.context.get('subscription')
        new_sub_type = attrs.get('new_subscription_type_id')
        
        if not subscription:
            raise serializers.ValidationError("Subscription is required")
            
        if new_sub_type.tier <= subscription.sub_type.tier:
            raise serializers.ValidationError(
                "New subscription must be of a higher tier"
            )
            
        return attrs
    
    def create(self, validated_data):
        subscription = self.context.get('subscription')
        new_sub_type = validated_data.get('new_subscription_type_id')
        
        return SubscriptionService.upgrade_subscription(
            subscription,
            new_sub_type.id
        )
