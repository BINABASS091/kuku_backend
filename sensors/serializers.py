from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from sensors.models import SensorType, Reading
from farms.models import Device

class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for Device model with basic validation.
    """
    class Meta:
        model = Device
        fields = ['deviceID', 'device_id', 'name', 'cell_no', 'picture', 'status']
        read_only_fields = ['deviceID', 'status']
        
    def validate_device_id(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Device ID cannot be empty."))
        return value.strip()


class SensorTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorType model with validation and computed fields.
    """
    total_readings = serializers.SerializerMethodField()
    active_devices_count = serializers.SerializerMethodField()
    latest_reading_timestamp = serializers.SerializerMethodField()
    avg_reading_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SensorType
        fields = ['sensorTypeID', 'sensorTypeName', 'measurementUnit', 'total_readings', 'active_devices_count', 
                 'latest_reading_timestamp', 'avg_reading_value']
        read_only_fields = ['sensorTypeID']
    
    def get_total_readings(self, obj):
        """Get total number of readings for this sensor type"""
        return obj.readings.count()
    
    def get_active_devices_count(self, obj):
        """Get number of active devices using this sensor type"""
        return obj.readings.filter(deviceID__status=True).values('deviceID').distinct().count()
    
    def get_latest_reading_timestamp(self, obj):
        """Get timestamp of the latest reading"""
        latest = obj.readings.order_by('-timestamp').first()
        return latest.timestamp if latest else None
    
    def get_avg_reading_value(self, obj):
        """Get average reading value for this sensor type"""
        from django.db.models import Avg
        result = obj.readings.aggregate(avg_value=Avg('value'))
        return round(result['avg_value'], 2) if result['avg_value'] else 0
        
    def validate_sensorTypeName(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Sensor type name cannot be empty."))
        return value.strip()
        
    def validate_measurementUnit(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Unit cannot be empty."))
        return value.strip()


class ReadingSerializer(serializers.ModelSerializer):
    """Reading serializer exposing legacy FK field names (deviceID, sensor_typeID)."""
    deviceID = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all(), source='deviceID')
    sensor_typeID = serializers.PrimaryKeyRelatedField(queryset=SensorType.objects.all(), source='sensor_typeID')
    device_detail = DeviceSerializer(source='deviceID', read_only=True)
    sensor_type_detail = SensorTypeSerializer(source='sensor_typeID', read_only=True)

    class Meta:
        model = Reading
        fields = [
            'readingID', 'deviceID', 'device_detail', 'sensor_typeID', 'sensor_type_detail',
            'value', 'timestamp'
        ]
        read_only_fields = ['readingID', 'timestamp']

    def validate_value(self, value):
        sensor_type = self.initial_data.get('sensor_typeID') or getattr(self.instance, 'sensor_typeID', None)
        try:
            st_obj = SensorType.objects.get(pk=sensor_type) if isinstance(sensor_type, int) else sensor_type
        except Exception:
            st_obj = None
        if st_obj and 'temp' in st_obj.name.lower() and (value < -50 or value > 100):
            raise ValidationError({"value": _("Temperature value out of range (-50 to 100).")})
        return value
