from django.shortcuts import render
from rest_framework import viewsets, permissions
from config.permissions import IsAdminOrReadOnly
from sensors.models import SensorType, Reading
from sensors.serializers import SensorTypeSerializer, ReadingSerializer

# Create your views here.

class SensorTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sensor types to be viewed or edited.
    """
    queryset = SensorType.objects.all()
    serializer_class = SensorTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        """
        Return a queryset with all sensor types.
        """
        return super().get_queryset()

class ReadingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sensor readings to be viewed or created.
    """
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['deviceID', 'sensor_typeID']
    search_fields = ['deviceID__name', 'sensor_typeID__name']
    ordering_fields = ['timestamp', 'value']
    ordering = ['-timestamp']

    def get_queryset(self):
        """
        Return a filtered queryset of readings based on query parameters.
        """
        queryset = Reading.objects.select_related(
            'deviceID', 
            'sensor_typeID'
        ).all()
        
        # Apply filters from query parameters
        device_id = self.request.query_params.get('device')
        sensor_type_id = self.request.query_params.get('sensor_type')
        from_ts = self.request.query_params.get('from')
        to_ts = self.request.query_params.get('to')
        
        if device_id:
            queryset = queryset.filter(deviceID=device_id)
        if sensor_type_id:
            queryset = queryset.filter(sensor_typeID=sensor_type_id)
        if from_ts:
            queryset = queryset.filter(timestamp__gte=from_ts)
        if to_ts:
            queryset = queryset.filter(timestamp__lte=to_ts)
            
        return queryset
