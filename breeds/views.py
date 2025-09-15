from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
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
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class BreedTypeViewSet(viewsets.ModelViewSet):
    queryset = BreedType.objects.all()
    serializer_class = BreedTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BreedViewSet(viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def create(self, request, *args, **kwargs):
        print(f"=== BREED CREATION DEBUG ===")
        print(f"Request data: {request.data}")
        print(f"Request content type: {request.content_type}")
        print(f"breed_typeID value: {request.data.get('breed_typeID')}")
        print(f"breed_typeID type: {type(request.data.get('breed_typeID'))}")
        print(f"All keys in request.data: {list(request.data.keys())}")
        print(f"=== END DEBUG ===")
        
        logger.info(f"Breed creation request data: {request.data}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"breed_typeID value: {request.data.get('breed_typeID')}")
        logger.info(f"breed_typeID type: {type(request.data.get('breed_typeID'))}")
        
        # Check if breed_typeID exists and is valid
        breed_type_id = request.data.get('breed_typeID')
        if breed_type_id is None or breed_type_id == '' or breed_type_id == 'null':
            logger.error(f"Breed type None does not exist")
            print(f"ERROR: breed_type_id is invalid: {breed_type_id}")
            return Response(
                {'breed_typeID': ['Breed type is required']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            breed_type = BreedType.objects.get(pk=breed_type_id)
            logger.info(f"Found breed type: {breed_type}")
            print(f"SUCCESS: Found breed type: {breed_type}")
        except BreedType.DoesNotExist:
            logger.error(f"Breed type {breed_type_id} does not exist")
            print(f"ERROR: Breed type {breed_type_id} does not exist")
            return Response(
                {'breed_typeID': ['Invalid breed type ID']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            logger.error(f"Invalid breed type ID format: {breed_type_id}, error: {e}")
            print(f"ERROR: Invalid breed type ID format: {breed_type_id}, error: {e}")
            return Response(
                {'breed_typeID': ['Invalid breed type ID format']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Breed serializer validation errors: {serializer.errors}")
            print(f"SERIALIZER ERRORS: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
