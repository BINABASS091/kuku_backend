from rest_framework import serializers
from batches.models import Batch, ActivitySchedule, BatchActivity, BatchFeeding
from farms.models import Farm
from breeds.models import Breed, BreedActivity
from breeds.serializers import BreedSerializer as BreedDetailSerializer

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['farmID', 'name', 'location']

# Use the detailed Breed serializer from breeds app (includes type_detail)
BreedSerializer = BreedDetailSerializer

class BreedActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BreedActivity
        fields = ['breedActivityID', 'breed', 'activity_type', 'age', 'breed_activity_status']

class BatchSerializer(serializers.ModelSerializer):
    farm = FarmSerializer(read_only=True)
    breed = BreedSerializer(read_only=True)
    
    class Meta:
        model = Batch
        fields = ['batchID', 'farm', 'breed', 'arrive_date', 'init_age', 'harvest_age', 'quanitity', 'init_weight', 'batch_status']

class ActivityScheduleSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    
    class Meta:
        model = ActivitySchedule
        fields = ['activityID', 'batch', 'activityName', 'activityDescription', 'activityDay', 'activity_status', 'activity_frequency']

class BatchActivitySerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    breed_activity = BreedActivitySerializer(read_only=True)
    
    class Meta:
        model = BatchActivity
        fields = ['batchActivityID', 'batch', 'breed_activity', 'batchActivityName', 'batchActivityDate', 'batchActivityDetails', 'batchAcitivtyCost']

class BatchFeedingSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    
    class Meta:
        model = BatchFeeding
        fields = ['batchFeedingID', 'batch', 'feedingDate', 'feedingAmount', 'status']
