from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for the knowledge app
router = DefaultRouter()

# Register ViewSets with the router
router.register(r'patient-healths', views.PatientHealthViewSet, basename='patient-health')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')
router.register(r'exception-diseases', views.ExceptionDiseaseViewSet, basename='exception-disease')
router.register(r'anomalies', views.AnomalyViewSet, basename='anomaly')
router.register(r'medications', views.MedicationViewSet, basename='medication')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]
