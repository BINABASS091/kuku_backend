from rest_framework import serializers
from batches.models import Batch, ActivitySchedule, BatchActivity
from farms.models import Farm
from breeds.models import Breed, BreedActivity
from breeds.serializers import BreedSerializer as BreedDetailSerializer

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['id', 'name', 'location']

# Use the detailed Breed serializer from breeds app (includes type_detail)
BreedSerializer = BreedDetailSerializer

class BreedActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BreedActivity
        fields = ['id', 'name', 'description']

class BatchSerializer(serializers.ModelSerializer):
    farm = FarmSerializer(read_only=True)
    breed = BreedSerializer(read_only=True)
    
    class Meta:
        model = Batch
        fields = '__all__'

class ActivityScheduleSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    
    class Meta:
        model = ActivitySchedule
        fields = '__all__'

class BatchActivitySerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    breed_activity = BreedActivitySerializer(read_only=True)
    
    class Meta:
        model = BatchActivity
        fields = '__all__'
