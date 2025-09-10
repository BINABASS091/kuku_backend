from django.db import models


class SubscriptionType(models.Model):
    TIER_CHOICES = [
        ('INDIVIDUAL', 'Individual/Small'),
        ('NORMAL', 'Normal/Medium'),
        ('PREMIUM', 'Premium/Large')
    ]
    
    id = models.AutoField(primary_key=True)  # Keep existing id field for migration compatibility
    subscriptionTypeID = models.IntegerField(unique=True, default=1)  # Will become primary key after migration
    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='INDIVIDUAL')
    farm_size = models.CharField(max_length=20, default='Small')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_hardware_nodes = models.PositiveIntegerField(default=1)
    max_software_services = models.PositiveIntegerField(default=1)
    includes_predictions = models.BooleanField(default=False)
    includes_analytics = models.BooleanField(default=False)
    description = models.TextField(default='No description')

    def __str__(self):
        return f'{self.get_tier_display()} - {self.name} ({self.farm_size})'


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
    id = models.AutoField(primary_key=True)  # Keep existing id field for migration compatibility
    resourceID = models.IntegerField(unique=True, default=1)  # Will become primary key after migration
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
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.BooleanField(default=True)
    is_basic = models.BooleanField(
        default=False,
        help_text='If True, this resource is available to all farmers regardless of subscription'
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['resource_type', 'name']

    def __str__(self):
        return f'{self.get_category_display()} - {self.name}'

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
    id = models.AutoField(primary_key=True)  # Keep existing id field for migration compatibility
    farmerSubscriptionID = models.IntegerField(unique=True, default=1)  # Will become primary key after migration
    farmerID = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='subscriptions', db_column='farmerID', null=True, blank=True)
    subscription_typeID = models.ForeignKey('subscriptions.SubscriptionType', on_delete=models.PROTECT, related_name='farmer_subscriptions', db_column='subscription_typeID', null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(default='1900-01-01')
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

    def __str__(self):
        return f'{self.farmerID.user.get_full_name()} - {self.subscription_typeID.name} ({self.status})'

    @property
    def is_active(self):
        from django.utils import timezone
        return (
            self.status == SubscriptionStatus.ACTIVE and 
            self.end_date >= timezone.now().date()
        )

    def get_utilization(self):
        """Get resource utilization for this subscription"""
        from django.db.models import Sum, Q
        
        resources = self.resources.filter(status=True).select_related('resource')
        
        hardware_count = resources.filter(resource__resource_type=ResourceType.HARDWARE).count()
        software_count = resources.filter(
            Q(resource__resource_type=ResourceType.SOFTWARE) |
            Q(resource__resource_type=ResourceType.PREDICTION) |
            Q(resource__resource_type=ResourceType.ANALYTICS)
        ).count()
        
        return {
            'hardware': {
                'used': hardware_count,
                'limit': self.sub_type.max_hardware_nodes,
                'available': max(0, self.sub_type.max_hardware_nodes - hardware_count)
            },
            'software': {
                'used': software_count,
                'limit': self.sub_type.max_software_services,
                'available': max(0, self.sub_type.max_software_services - software_count)
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

class FarmerSubscriptionResource(models.Model):
    id = models.AutoField(primary_key=True)  # Keep existing id field for migration compatibility
    farmerSubscriptionResourceID = models.IntegerField(unique=True, default=1)  # Will become primary key after migration
    farmerSubscriptionID = models.ForeignKey(
        'subscriptions.FarmerSubscription', 
        on_delete=models.CASCADE, 
        related_name='resources',
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

    def __str__(self):
        return f'{self.farmerSubscriptionID} - {self.resourceID} ({self.quantity})'
        if not self.pk:  # Only check for new instances
            if not self.resource.is_basic and not self.farmer_subscription.can_add_resource(self.resource):
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    'Cannot add more resources of this type. '
                    'Please upgrade your subscription or contact support.'
                )
        super().save(*args, **kwargs)

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'

class Payment(models.Model):
    id = models.AutoField(primary_key=True)  # Keep existing id field for migration compatibility
    paymentID = models.IntegerField(unique=True, default=1)  # Will become primary key after migration
    farmerSubscriptionID = models.ForeignKey(
        'subscriptions.FarmerSubscription', 
        on_delete=models.CASCADE, 
        related_name='payments',
        db_column='farmerSubscriptionID',
        null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(default='1900-01-01')
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

    def __str__(self):
        return f'{self.farmerSubscriptionID} - {self.amount} ({self.status})'

# Create your models here.
