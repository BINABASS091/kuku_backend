from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter
from subscriptions.views import SubscriptionStatusView, SubscriptionStatsView, BillingReportsView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .dashboard import dashboard_stats
# Temporarily commented out to fix circular import during migrations
# from .views import SystemConfigurationViewSet, SystemLogViewSet, BackupRecordViewSet, SystemMetricsView


router = DefaultRouter()

# Import all ViewSets
from accounts.views import UserViewSet, FarmerViewSet
from farms.views import FarmViewSet, DeviceViewSet
from breeds.views import (
    BreedTypeViewSet, BreedViewSet, ActivityTypeViewSet, BreedActivityViewSet,
    ConditionTypeViewSet, BreedConditionViewSet, FoodTypeViewSet, 
    BreedFeedingViewSet, BreedGrowthViewSet, BreedConfigurationViewSet, FarmBreedPlanViewSet
)
from batches.views import BatchViewSet, ActivityScheduleViewSet, BatchActivityViewSet, BatchFeedingViewSet
from subscriptions.views import (
    SubscriptionTypeViewSet, ResourceViewSet, FarmerSubscriptionViewSet,
    FarmerSubscriptionResourceViewSet, PaymentViewSet
)
from sensors.views import SensorTypeViewSet, ReadingViewSet
from knowledge.views import (
    PatientHealthViewSet, RecommendationViewSet, ExceptionDiseaseViewSet,
    AnomalyViewSet, MedicationViewSet
)

# Register all ViewSets
router.register(r'users', UserViewSet)
router.register(r'farmers', FarmerViewSet)
router.register(r'farms', FarmViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'breed-types', BreedTypeViewSet)
router.register(r'breeds', BreedViewSet)
router.register(r'breed-configurations', BreedConfigurationViewSet)
router.register(r'farm-breed-plans', FarmBreedPlanViewSet)
router.register(r'activity-types', ActivityTypeViewSet)
router.register(r'breed-activities', BreedActivityViewSet)
router.register(r'condition-types', ConditionTypeViewSet)
router.register(r'breed-conditions', BreedConditionViewSet)
router.register(r'food-types', FoodTypeViewSet)
router.register(r'breed-feedings', BreedFeedingViewSet)
router.register(r'breed-growths', BreedGrowthViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'activity-schedules', ActivityScheduleViewSet)
router.register(r'batch-activities', BatchActivityViewSet)
router.register(r'batch-feedings', BatchFeedingViewSet)
router.register(r'subscription-types', SubscriptionTypeViewSet)
router.register(r'resources', ResourceViewSet)
# Subscription endpoints
# Register the main subscription views first
router.register(r'farmer-subscriptions', FarmerSubscriptionViewSet, basename='farmer-subscription')

# Nested subscription resources - must be after parent registration
subscription_router = NestedSimpleRouter(router, r'farmer-subscriptions', lookup='subscription')
subscription_router.register(r'resources', FarmerSubscriptionResourceViewSet, basename='subscription-resource')

# Register remaining views
router.register(r'payments', PaymentViewSet)
router.register(r'sensor-types', SensorTypeViewSet)
router.register(r'readings', ReadingViewSet)
router.register(r'patient-healths', PatientHealthViewSet)
router.register(r'recommendations', RecommendationViewSet)
router.register(r'exception-diseases', ExceptionDiseaseViewSet)
router.register(r'anomalies', AnomalyViewSet)
router.register(r'medications', MedicationViewSet)

# System Administration ViewSets - temporarily commented out for migrations
# router.register(r'system/configuration', SystemConfigurationViewSet, basename='system-configuration')
# router.register(r'system/logs', SystemLogViewSet, basename='system-logs')
# router.register(r'system/backups', BackupRecordViewSet, basename='system-backups')

urlpatterns = [
    # Include nested router URLs FIRST so they match before action-based routes
    path('', include(subscription_router.urls)),
    path('', include(router.urls)),
    path('', include('knowledge.urls')),
    # Dashboard endpoints
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    # Subscription-specific endpoints
    path('subscriptions/stats/', SubscriptionStatsView.as_view(), name='subscription-stats'),
    path('billing-reports/', BillingReportsView.as_view(), name='billing-reports'),
    # System Administration endpoints - temporarily commented out for migrations
    # path('system/metrics/', SystemMetricsView.as_view(), name='system-metrics'),
    # APIView endpoints
    path('subscription-status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
