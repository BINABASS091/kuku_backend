from rest_framework import serializers
from .models import Farm, Device


class FarmSerializer(serializers.ModelSerializer):
	class Meta:
		model = Farm
		fields = [
			'farmID', 'name', 'location', 'size', 'farmer'
		]


class DeviceSerializer(serializers.ModelSerializer):
	class Meta:
		model = Device
		fields = [
			'deviceID', 'device_id', 'name', 'cell_no', 'picture', 'status', 'farm'
		]

