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
        fields = ['id', 'device_id', 'name', 'cell_no', 'picture', 'status']
        read_only_fields = ['id', 'status']
        
    def validate_device_id(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Device ID cannot be empty."))
        return value.strip()


class SensorTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorType model with validation.
    """
    class Meta:
        model = SensorType
        fields = '__all__'
        read_only_fields = ['id']
        
    def validate_name(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Sensor type name cannot be empty."))
        return value.strip()
        
    def validate_unit(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Unit cannot be empty."))
        return value.strip()


class ReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for Reading model with validation and nested representations.
    """
    device = DeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True,
        help_text=_("ID of the device that generated this reading")
    )
    
    sensor_type = SensorTypeSerializer(read_only=True)
    sensor_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SensorType.objects.all(),
        source='sensor_type',
        write_only=True,
        help_text=_("ID of the sensor type for this reading")
    )
    
    class Meta:
        model = Reading
        fields = [
            'id', 'device', 'device_id', 'sensor_type', 'sensor_type_id', 
            'value', 'timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, data):
        """
        Validate the reading data.
        """
        # Ensure device and sensor_type are provided for creation
        if self.instance is None:
            if 'device' not in data:
                raise ValidationError({"device_id": _("This field is required.")})
            if 'sensor_type' not in data:
                raise ValidationError({"sensor_type_id": _("This field is required.")})
                
        # Validate value is within reasonable bounds
        value = data.get('value')
        if value is not None:
            # Get sensor type to validate value range if needed
            sensor_type = data.get('sensor_type') or getattr(self.instance, 'sensor_type', None)
            if sensor_type:
                # Example: Validate temperature range
                if 'temp' in sensor_type.name.lower() and (value < -50 or value > 100):
                    raise ValidationError({
                        "value": _("Temperature value out of range (-50 to 100).")
                    })
                # Add more sensor-specific validations as needed
                
        return data
        
    def create(self, validated_data):
        """
        Create a new reading with the validated data.
        """
        try:
            return super().create(validated_data)
        except Exception as e:
            raise ValidationError({"detail": _("Failed to create reading: {}".format(str(e)))})
            
    def update(self, instance, validated_data):
        """
        Update an existing reading with the validated data.
        """
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            raise ValidationError({"detail": _("Failed to update reading: {}".format(str(e)))})
