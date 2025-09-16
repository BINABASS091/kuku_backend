from rest_framework import serializers
from batches.models import Batch, ActivitySchedule, BatchActivity, BatchFeeding
from farms.models import Farm
from breeds.models import Breed, BreedActivity, ActivityType
from breeds.serializers import BreedSerializer as LegacyBreedSerializer


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['farmID', 'farmName', 'location']


class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ['breedID', 'breedName']


class BreedActivitySerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    activityTypeID = serializers.PrimaryKeyRelatedField(queryset=ActivityType.objects.all())

    class Meta:
        model = BreedActivity
        fields = ['breedActivityID', 'breedID', 'activityTypeID', 'age', 'breed_activity_status']
        read_only_fields = ['breedActivityID']


class BatchSerializer(serializers.ModelSerializer):
    farmID = serializers.PrimaryKeyRelatedField(queryset=Farm.objects.all())
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    farm_details = FarmSerializer(source='farmID', read_only=True)
    breed_details = BreedSerializer(source='breedID', read_only=True)
    # Use actual DB column names (arriveDate, initAge, harvestAge, initWeight)

    class Meta:
        model = Batch
        fields = [
            'batchID', 'farmID', 'breedID', 'arriveDate', 'initAge', 'harvestAge',
            'quanitity', 'initWeight', 'batch_status', 'farm_details', 'breed_details'
        ]
        read_only_fields = ['batchID']


class ActivityScheduleSerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        model = ActivitySchedule
        fields = [
            'activityID', 'batchID', 'activityName', 'activityDescription',
            'activityDay', 'activity_status', 'activity_frequency'
        ]
        read_only_fields = ['activityID']


class BatchActivitySerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    breedActivityID = serializers.PrimaryKeyRelatedField(queryset=BreedActivity.objects.all())

    class Meta:
        model = BatchActivity
        fields = [
            'batchActivityID', 'batchID', 'breedActivityID', 'batchActivityName',
            'batchActivityDate', 'batchActivityDetails', 'batchAcitivtyCost'
        ]
        read_only_fields = ['batchActivityID']


class BatchFeedingSerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        model = BatchFeeding
        fields = ['batchFeedingID', 'batchID', 'feedingDate', 'feedingAmount', 'status']
        read_only_fields = ['batchFeedingID']
