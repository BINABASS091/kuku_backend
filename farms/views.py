from rest_framework import viewsets, permissions
from .models import Farm, Device
from .serializers import FarmSerializer, DeviceSerializer


class FarmViewSet(viewsets.ModelViewSet):
	queryset = Farm.objects.select_related('farmer').all()
	serializer_class = FarmSerializer
	permission_classes = [permissions.IsAuthenticated]


class DeviceViewSet(viewsets.ModelViewSet):
	queryset = Device.objects.select_related('farm').all()
	serializer_class = DeviceSerializer
	permission_classes = [permissions.IsAuthenticated]

# Create your views here.
