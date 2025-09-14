from django.shortcuts import render
from rest_framework import viewsets, permissions
from knowledge.models import (
    PatientHealth, Recommendation, ExceptionDisease, 
    Anomaly, Medication
)
from knowledge.serializers import (
    PatientHealthSerializer, RecommendationSerializer, ExceptionDiseaseSerializer,
    AnomalySerializer, MedicationSerializer
)
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce

# Create your views here.

class PatientHealthViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows patient health conditions to be viewed or edited.
    """
    queryset = PatientHealth.objects.all()
    serializer_class = PatientHealthSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['description']
    ordering_fields = ['description']
    ordering = ['description']
    
    def get_queryset(self):
        """
        Return a queryset with all patient health conditions.
        """
        return PatientHealth.objects.all()

class RecommendationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows recommendations to be viewed or edited.
    """
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['description', 'reco_type', 'context']
    filterset_fields = ['reco_type', 'context']
    ordering_fields = ['description', 'reco_type']
    ordering = ['description']
    
    def get_queryset(self):
        """
        Return a queryset with all recommendations.
        """
        return Recommendation.objects.all()

class ExceptionDiseaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows disease exceptions to be viewed or edited.
    """
    queryset = ExceptionDisease.objects.all()
    serializer_class = ExceptionDiseaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return a queryset with all disease exceptions and related data.
        """
        return ExceptionDisease.objects.select_related(
            'recommendation',
            'health'
        ).all()

class AnomalyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows anomalies to be viewed or edited.
    """
    queryset = Anomaly.objects.all()
    serializer_class = AnomalySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['id']
    ordering = ['-id']
    
    def get_queryset(self):
        """
        Return a queryset with all anomalies.
        """
        return Anomaly.objects.all()

class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows medications to be viewed or edited.
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['diagnosis', 'user', 'sequence_no']
    ordering_fields = ['sequence_no', 'diagnosis']
    ordering = ['diagnosis', 'sequence_no']
    
    def get_queryset(self):
        """
        Return a queryset with all medications and related data.
        """
        return Medication.objects.select_related(
            'diagnosis',
            'recommendation',
            'user'
        ).all()

class HealthConditionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows health conditions to be viewed or edited.
    """
    queryset = PatientHealth.objects.all()
    serializer_class = PatientHealthSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return a queryset with all health conditions.
        """
        return PatientHealth.objects.all()

    def get_total_allocations(self, obj):
        try:
            # Aggregate over resource_allocations and sum the quantity field
            result = obj.resource_allocations.aggregate(total=Sum('quantity'))
            return result['total'] or 0
        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error in get_total_allocations: {e}")
            return 0
