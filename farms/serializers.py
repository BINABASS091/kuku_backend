from rest_framework import serializers
from .models import Farm, Device
from accounts.serializers import FarmerSerializer
from accounts.models import Farmer


class DeviceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['deviceID', 'device_id', 'name', 'cell_no', 'picture', 'status']



# New: FarmMembership serializer
from .models import FarmMembership

class FarmMembershipSerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer(read_only=True)
    class Meta:
        model = FarmMembership
        fields = ['id', 'farmer', 'role', 'joined_at']


class FarmSerializer(serializers.ModelSerializer):
    memberships = FarmMembershipSerializer(many=True, read_only=True)
    devices = DeviceListSerializer(many=True, read_only=True, source='farm_devices')
    total_devices = serializers.SerializerMethodField()
    active_devices = serializers.SerializerMethodField()
    total_batches = serializers.SerializerMethodField()
    active_batches = serializers.SerializerMethodField()
    total_birds = serializers.SerializerMethodField()
    last_activity_date = serializers.SerializerMethodField()
    farm_status = serializers.SerializerMethodField()
    myRole = serializers.SerializerMethodField()

    class Meta:
        model = Farm
        fields = [
            'farmID', 'farmName', 'location', 'farmSize', 'memberships',
            'devices', 'total_devices', 'active_devices', 'total_batches', 
            'active_batches', 'total_birds', 'last_activity_date', 'farm_status', 'myRole'
        ]
        read_only_fields = ['farmID']

    def get_myRole(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'farmer_profile'):
            return None
        farmer = request.user.farmer_profile
        membership = obj.memberships.filter(farmer=farmer).first()
        if membership:
            return membership.role
        return None

    def validate_farmSize(self, value):
        if not value:
            raise serializers.ValidationError("Farm size is required.")
        return value

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

    def create(self, validated_data):
        """Create farm and automatically add the creator as OWNER"""
        request = self.context.get('request')
        farm = super().create(validated_data)
        
        # Automatically create FarmMembership for the creator as OWNER
        if request and hasattr(request.user, 'farmer_profile'):
            FarmMembership.objects.create(
                farmer=request.user.farmer_profile,
                farm=farm,
                role='OWNER'
            )
        
        return farm


class DeviceSerializer(serializers.ModelSerializer):
    farmID = serializers.PrimaryKeyRelatedField(queryset=Farm.objects.all())
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
        """Get farm details for the device"""
        try:
            if obj.farmID:
                return {
                    'farmID': obj.farmID.id,
                    'location': obj.farmID.location,
                    'farmName': obj.farmID.farmName,
                }
            return None
        except:
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

