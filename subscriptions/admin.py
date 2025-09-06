from django.contrib import admin
from .models import SubscriptionType, Resource, FarmerSubscription, FarmerSubscriptionResource, Payment


admin.site.register(SubscriptionType)
admin.site.register(Resource)
admin.site.register(FarmerSubscription)
admin.site.register(FarmerSubscriptionResource)
admin.site.register(Payment)

# Register your models here.
