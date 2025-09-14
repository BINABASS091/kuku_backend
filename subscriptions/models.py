from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q


class SubscriptionType(models.Model):
    TIER_CHOICES = [
        ('INDIVIDUAL', 'Individual/Small'),
        ('NORMAL', 'Normal/Medium'),
        ('PREMIUM', 'Premium/Large')
    ]

    subscriptionTypeID = models.AutoField(primary_key=True, db_column='subscriptionTypeID')
    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='INDIVIDUAL')
    farm_size = models.CharField(max_length=20, default='Small')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_hardware_nodes = models.PositiveIntegerField(default=1)
    max_software_services = models.PositiveIntegerField(default=1)
    includes_predictions = models.BooleanField(default=False)
    includes_analytics = models.BooleanField(default=False)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'subscription_type_tb'
        ordering = ['tier', 'name']

    def __str__(self):
        return f'{self.tier} - {self.name} ({self.farm_size})'

    # Compatibility alias for serializers expecting .id
    @property
    def id(self):  # pragma: no cover
        return self.subscriptionTypeID


class ResourceType(models.TextChoices):
    HARDWARE = 'HARDWARE', 'Hardware Node'
    SOFTWARE = 'SOFTWARE', 'Software Service'
    PREDICTION = 'PREDICTION', 'Prediction Service'
    ANALYTICS = 'ANALYTICS', 'Analytics Service'

class ResourceCategory(models.TextChoices):
    FEEDING = 'FEEDING', 'Feeding Node'
    THERMAL = 'THERMAL', 'Thermal Node'
    WATERING = 'WATERING', 'Watering Node'
    WEIGHTING = 'WEIGHTING', 'Weighting Node'
    DUSTING = 'DUSTING', 'Dusting Node'
    PREDICTION = 'PREDICTION', 'Prediction Service'
    ANALYTICS = 'ANALYTICS', 'Analytics Service'
    INVENTORY = 'INVENTORY', 'Inventory Management'

class Resource(models.Model):
    resourceID = models.AutoField(primary_key=True, db_column='resourceID')
    name = models.CharField(max_length=50, unique=True, default='Default Resource')
    resource_type = models.CharField(
        max_length=20, 
        choices=ResourceType.choices,
        default=ResourceType.HARDWARE
    )
    category = models.CharField(
        max_length=20,
        choices=ResourceCategory.choices,
        default=ResourceCategory.INVENTORY
    )
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.BooleanField(default=True)
    is_basic = models.BooleanField(
        default=False,
        help_text='If True, this resource is available to all farmers regardless of subscription'
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscription_resources = models.ManyToManyField(
        'subscriptions.FarmerSubscription',
        through='FarmerSubscriptionResource',
        related_name='resource_allocations',  # Updated related_name to avoid clashes
        help_text='Subscriptions that use this resource'
    )

    class Meta:
        ordering = ['resource_type', 'name']
        db_table = 'resource_tb'
        indexes = [
            models.Index(fields=['resource_type', 'category'], name='resource_type_category_idx')
        ]

    def __str__(self):
        return f'{self.category} - {self.name}'

    @property
    def id(self):  # pragma: no cover
        return self.resourceID

    def is_hardware(self):
        return self.resource_type == ResourceType.HARDWARE

    def is_software(self):
        return self.resource_type in [ResourceType.SOFTWARE, 
                                    ResourceType.PREDICTION, 
                                    ResourceType.ANALYTICS]


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PENDING = 'PENDING', 'Pending Payment'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'

class FarmerSubscription(models.Model):
    farmerSubscriptionID = models.AutoField(primary_key=True, db_column='farmerSubscriptionID')
    farmerID = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='subscriptions', db_column='farmerID', null=True, blank=True)
    subscription_typeID = models.ForeignKey('subscriptions.SubscriptionType', on_delete=models.PROTECT, related_name='farmer_subscriptions', db_column='subscription_typeID', null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING
    )
    auto_renew = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Farmer Subscription'
        verbose_name_plural = 'Farmer Subscriptions'
        db_table = 'farmer_subscription_tb'
        indexes = [
            models.Index(fields=['status', 'start_date'], name='subscription_status_start_idx')
        ]

    def __str__(self):
        farmer_name = None
        if self.farmerID and getattr(self.farmerID, 'user', None):
            farmer_name = self.farmerID.user.get_full_name() or str(self.farmerID.user)
        elif self.farmerID:
            farmer_name = str(self.farmerID)
        else:
            farmer_name = 'Unknown Farmer'
        sub_name = self.subscription_typeID.name if self.subscription_typeID else 'No Plan'
        return f'{farmer_name} - {sub_name} ({self.status})'

    @property
    def is_active(self):
        from django.utils import timezone
        return (
            self.status == SubscriptionStatus.ACTIVE and 
            (self.end_date is None or self.end_date >= timezone.now().date())
        )

    def get_utilization(self):
        """Get resource utilization for this subscription"""
        # type: ignore[attr-defined] for reverse relation during static analysis
        resources_qs = self.resources.filter(status=True).select_related('resourceID')  # type: ignore[attr-defined]
        hardware_count = resources_qs.filter(resourceID__resource_type=ResourceType.HARDWARE).count()
        software_count = resources_qs.filter(
            Q(resourceID__resource_type=ResourceType.SOFTWARE) |
            Q(resourceID__resource_type=ResourceType.PREDICTION) |
            Q(resourceID__resource_type=ResourceType.ANALYTICS)
        ).count()
        hw_limit = self.subscription_typeID.max_hardware_nodes if self.subscription_typeID else 0
        sw_limit = self.subscription_typeID.max_software_services if self.subscription_typeID else 0
        return {
            'hardware': {
                'used': hardware_count,
                'limit': hw_limit,
                'available': max(0, hw_limit - hardware_count)
            },
            'software': {
                'used': software_count,
                'limit': sw_limit,
                'available': max(0, sw_limit - software_count)
            }
        }

    def can_add_resource(self, resource):
        """Check if a resource can be added to this subscription"""
        if resource.is_basic:
            return True
            
        utilization = self.get_utilization()
        
        if resource.is_hardware():
            return utilization['hardware']['available'] > 0
        else:  # Software, Prediction, or Analytics
            return utilization['software']['available'] > 0

    # Backwards compatibility aliases
    @property
    def id(self):  # pragma: no cover
        return self.farmerSubscriptionID

    @property
    def sub_type(self):  # pragma: no cover
        return self.subscription_typeID

    @property
    def farmer(self):  # pragma: no cover
        return self.farmerID

class FarmerSubscriptionResource(models.Model):
    farmerSubscriptionResourceID = models.AutoField(primary_key=True, db_column='farmerSubscriptionResourceID')
    farmerSubscriptionID = models.ForeignKey(
        'subscriptions.FarmerSubscription', 
        on_delete=models.CASCADE, 
        related_name='subscription_resources',  # Updated related_name to avoid clashes
        db_column='farmerSubscriptionID',
        null=True, blank=True
    )
    resourceID = models.ForeignKey(
        'subscriptions.Resource', 
        on_delete=models.PROTECT, 
        related_name='allocations',
        db_column='resourceID',
        null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    status = models.BooleanField(default=True)
    allocated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['farmerSubscriptionID', 'resourceID']
        verbose_name = 'Subscription Resource'
        verbose_name_plural = 'Subscription Resources'
        db_table = 'farmer_subscription_resource_tb'
        indexes = [
            models.Index(fields=['farmerSubscriptionID', 'resourceID']),
            models.Index(fields=['status'], name='sub_res_status_idx')
        ]

    def __str__(self):
        return f'{self.farmerSubscriptionID} - {self.resourceID} ({self.quantity})'

    def save(self, *args, **kwargs):
        # Validation (only on create)
        if self._state.adding and self.resourceID and self.farmerSubscriptionID:
            resource = self.resourceID
            subscription = self.farmerSubscriptionID
            if (not resource.is_basic) and (not subscription.can_add_resource(resource)):
                from django.core.exceptions import ValidationError
                raise ValidationError('Cannot add more resources of this type. Upgrade subscription.')
        super().save(*args, **kwargs)

    # Aliases for legacy serializer/service expectations
    @property
    def id(self):  # pragma: no cover
        return self.farmerSubscriptionResourceID

    @property
    def resource(self):  # pragma: no cover
        return self.resourceID

    @property
    def farmer_subscription(self):  # pragma: no cover
        return self.farmerSubscriptionID

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'

class Payment(models.Model):
    paymentID = models.AutoField(primary_key=True, db_column='paymentID')
    farmerSubscriptionID = models.ForeignKey(
        'subscriptions.FarmerSubscription', 
        on_delete=models.CASCADE, 
        related_name='payments',
        db_column='farmerSubscriptionID',
        null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    receipt = models.FileField(upload_to='payments/receipts/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        db_table = 'payment_tb'

    def __str__(self):
        return f'{self.farmerSubscriptionID} - {self.amount} ({self.status})'

    @property
    def id(self):  # pragma: no cover
        return self.paymentID

    # Compatibility aliases (used in permissions / legacy code)
    @property
    def subscription(self):  # pragma: no cover
        return self.farmerSubscriptionID

    @property
    def farmer_subscription(self):  # pragma: no cover
        return self.farmerSubscriptionID

    @property
    def farmer(self):  # pragma: no cover
        return self.farmerSubscriptionID.farmerID if self.farmerSubscriptionID else None

# Create your models here.
