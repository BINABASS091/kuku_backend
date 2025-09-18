from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Farm, Device
from .serializers import FarmSerializer, DeviceSerializer



from .models import FarmMembership

class FarmViewSet(viewsets.ModelViewSet):
	queryset = Farm.objects.none()  # Required for DRF router registration
	serializer_class = FarmSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		"""Return only farms where the user is a member (via FarmMembership)."""
		user = self.request.user
		print("DEBUG: user", user, user.id)
		print("DEBUG: user.hasattr(farmer_profile)", hasattr(user, 'farmer_profile'))
		if not hasattr(user, 'farmer_profile'):
			print("DEBUG: user has no farmer_profile")
			return Farm.objects.none()
		farmer = user.farmer_profile
		print("DEBUG: farmer", farmer, farmer.id)
		farm_ids = FarmMembership.objects.filter(farmer=farmer).values_list('farm_id', flat=True)
		print("DEBUG: farm_ids", list(farm_ids))
		return Farm.objects.filter(farmID__in=farm_ids).prefetch_related('farm_devices', 'memberships')

	@action(detail=True, methods=['get'])
	def statistics(self, request, pk=None):
		farm = self.get_object()
		data = {
			'total_devices': farm.farm_devices.count(),
			'active_devices': farm.farm_devices.filter(status=True).count(),
		}
		# Add user's role for this farm
		user = request.user
		role = None
		if hasattr(user, 'farmer_profile'):
			membership = FarmMembership.objects.filter(farmer=user.farmer_profile, farm=farm).first()
			if membership:
				role = membership.role
		data['your_role'] = role
		return Response(data)


class DeviceViewSet(viewsets.ModelViewSet):
	queryset = Device.objects.select_related('farmID').all()
	serializer_class = DeviceSerializer
	permission_classes = [permissions.IsAuthenticated]

# Create your views here.
