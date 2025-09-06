from django.shortcuts import render
from rest_framework import viewsets, permissions
from config.permissions import IsAdminOrReadOnly
from breeds.models import (
    BreedType, Breed, ActivityType, BreedActivity, 
    ConditionType, BreedCondition, FoodType, BreedFeeding, BreedGrowth
)
from breeds.serializers import (
    BreedTypeSerializer, BreedSerializer, ActivityTypeSerializer, BreedActivitySerializer,
    ConditionTypeSerializer, BreedConditionSerializer, FoodTypeSerializer, 
    BreedFeedingSerializer, BreedGrowthSerializer
)

# Create your views here.

class BreedTypeViewSet(viewsets.ModelViewSet):
    queryset = BreedType.objects.all()
    serializer_class = BreedTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BreedViewSet(viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [IsAdminOrReadOnly]

class ActivityTypeViewSet(viewsets.ModelViewSet):
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BreedActivityViewSet(viewsets.ModelViewSet):
    queryset = BreedActivity.objects.all()
    serializer_class = BreedActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

class ConditionTypeViewSet(viewsets.ModelViewSet):
    queryset = ConditionType.objects.all()
    serializer_class = ConditionTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BreedConditionViewSet(viewsets.ModelViewSet):
    queryset = BreedCondition.objects.all()
    serializer_class = BreedConditionSerializer
    permission_classes = [permissions.IsAuthenticated]

class FoodTypeViewSet(viewsets.ModelViewSet):
    queryset = FoodType.objects.all()
    serializer_class = FoodTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BreedFeedingViewSet(viewsets.ModelViewSet):
    queryset = BreedFeeding.objects.all()
    serializer_class = BreedFeedingSerializer
    permission_classes = [permissions.IsAuthenticated]

class BreedGrowthViewSet(viewsets.ModelViewSet):
    queryset = BreedGrowth.objects.all()
    serializer_class = BreedGrowthSerializer
    permission_classes = [permissions.IsAuthenticated]
