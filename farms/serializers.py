from rest_framework import serializers
from .models import Farm, Device
from accounts.serializers import FarmerSerializer


class DeviceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['deviceID', 'device_id', 'name', 'cell_no', 'picture', 'status']


class FarmSerializer(serializers.ModelSerializer):
    farmerID = serializers.PrimaryKeyRelatedField(queryset=Farm._meta.get_field('farmer').remote_field.model.objects.all(), source='farmer')
    farmer_details = serializers.SerializerMethodField()
    devices = DeviceListSerializer(many=True, read_only=True, source='farm_devices')
    total_devices = serializers.SerializerMethodField()
    active_devices = serializers.SerializerMethodField()
    total_batches = serializers.SerializerMethodField()
    active_batches = serializers.SerializerMethodField()
    total_birds = serializers.SerializerMethodField()
    last_activity_date = serializers.SerializerMethodField()
    farm_status = serializers.SerializerMethodField()

    class Meta:
        model = Farm
        fields = [
            'farmID', 'name', 'location', 'size', 'farmerID', 'farmer_details',
            'devices', 'total_devices', 'active_devices', 'total_batches', 
            'active_batches', 'total_birds', 'last_activity_date', 'farm_status'
        ]
        read_only_fields = ['farmID']

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be a positive number.")
        return value

    def get_farmer_details(self, obj):
        if hasattr(obj, 'farmer') and obj.farmer:
            return {
                'id': obj.farmer.id,
                'full_name': obj.farmer.full_name,
                'email': obj.farmer.email,
                'phone': obj.farmer.phone,
                'username': obj.farmer.user.username if obj.farmer.user else None
            }
        return None

    def get_total_devices(self, obj):
        return obj.farm_devices.count()

    def get_active_devices(self, obj):
        return obj.farm_devices.filter(status=True).count()

    def get_total_batches(self, obj):
        return getattr(obj, 'batches', obj.__class__.objects.none()).count()

    def get_active_batches(self, obj):
        try:
            return obj.batches.filter(batch_status=1).count()  # Status.ACTIVE = 1
        except:
            return 0

    def get_total_birds(self, obj):
        try:
            total = 0
            for batch in obj.batches.filter(batch_status=1):  # Only active batches
                total += batch.quanitity
            return total
        except:
            return 0

    def get_last_activity_date(self, obj):
        try:
            latest_batch = obj.batches.order_by('-arriveDate').first()
            if latest_batch:
                return latest_batch.arriveDate.isoformat()
            return None
        except:
            return None

    def get_farm_status(self, obj):
        active_devices = self.get_active_devices(obj)
        total_devices = self.get_total_devices(obj)
        active_batches = self.get_active_batches(obj)
        
        if total_devices == 0:
            return 'Setup Required'
        elif active_devices == total_devices and active_batches > 0:
            return 'Active'
        elif active_devices > 0:
            return 'Partial'
        else:
            return 'Inactive'

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except serializers.ValidationError as e:
            self.context['validation_error'] = e.detail
            raise e


class DeviceSerializer(serializers.ModelSerializer):
    farmID = serializers.PrimaryKeyRelatedField(queryset=Farm.objects.all(), source='farm')
    farm_details = serializers.SerializerMethodField()
    last_reading = serializers.SerializerMethodField()
    readings_count = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            'deviceID', 'device_id', 'name', 'cell_no', 'picture', 'status', 
            'farmID', 'farm_details', 'last_reading', 'readings_count'
        ]
        read_only_fields = ['deviceID']

    def get_farm_details(self, obj):
        if obj.farm:
            return {
                'farmID': obj.farm.farmID,
                'name': obj.farm.name,
                'location': obj.farm.location,
                'farmer_name': obj.farm.farmer.full_name if obj.farm.farmer else None
            }
        return None

    def get_last_reading(self, obj):
        try:
            if hasattr(obj, 'readings') and obj.readings.exists():
                last_reading = obj.readings.order_by('-created_at').first()
                return {
                    'timestamp': last_reading.created_at.isoformat(),
                    'value': last_reading.value,
                    'unit': last_reading.sensorType.unit if last_reading.sensorType else None
                }
            return None
        except:
            return None

    def get_readings_count(self, obj):
        try:
            return obj.readings.count() if hasattr(obj, 'readings') else 0
        except:
            return 0

