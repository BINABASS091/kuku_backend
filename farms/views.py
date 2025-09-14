from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Farm, Device
from .serializers import FarmSerializer, DeviceSerializer


class FarmViewSet(viewsets.ModelViewSet):
	queryset = Farm.objects.select_related('farmer').prefetch_related('farm_devices').all()
	serializer_class = FarmSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=True, methods=['get'])
	def statistics(self, request, pk=None):
		farm = self.get_object()
		data = {
			'total_devices': farm.farm_devices.count(),
			'active_devices': farm.farm_devices.filter(status=True).count(),
		}
		return Response(data)


class DeviceViewSet(viewsets.ModelViewSet):
	queryset = Device.objects.select_related('farm').all()
	serializer_class = DeviceSerializer
	permission_classes = [permissions.IsAuthenticated]

# Create your views here.
