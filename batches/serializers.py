from rest_framework import serializers
from batches.models import Batch, ActivitySchedule, BatchActivity, BatchFeeding
from farms.models import Farm
from breeds.models import Breed, BreedActivity, ActivityType
from breeds.serializers import BreedSerializer as LegacyBreedSerializer


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['farmID', 'name', 'location']


class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ['breedID', 'breedName']


class BreedActivitySerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    activityTypeID = serializers.PrimaryKeyRelatedField(queryset=ActivityType.objects.all(), source='activityTypeID')

    class Meta:
        model = BreedActivity
        fields = ['breedActivityID', 'breedID', 'activityTypeID', 'age', 'breed_activity_status']
        read_only_fields = ['breedActivityID']


class BatchSerializer(serializers.ModelSerializer):
    farmID = serializers.PrimaryKeyRelatedField(queryset=Farm.objects.all(), source='farmID')
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    # Use actual DB column names (arriveDate, initAge, harvestAge, initWeight)

    class Meta:
        model = Batch
        fields = [
            'batchID', 'farmID', 'breedID', 'arriveDate', 'initAge', 'harvestAge',
            'quanitity', 'initWeight', 'batch_status'
        ]
        read_only_fields = ['batchID']


class ActivityScheduleSerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), source='batchID')

    class Meta:
        model = ActivitySchedule
        fields = [
            'activityID', 'batchID', 'activityName', 'activityDescription',
            'activityDay', 'activity_status', 'activity_frequency'
        ]
        read_only_fields = ['activityID']


class BatchActivitySerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), source='batchID')
    breedActivityID = serializers.PrimaryKeyRelatedField(queryset=BreedActivity.objects.all(), source='breedActivityID')

    class Meta:
        model = BatchActivity
        fields = [
            'batchActivityID', 'batchID', 'breedActivityID', 'batchActivityName',
            'batchActivityDate', 'batchActivityDetails', 'batchAcitivtyCost'
        ]
        read_only_fields = ['batchActivityID']


class BatchFeedingSerializer(serializers.ModelSerializer):
    batchID = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), source='batchID')

    class Meta:
        model = BatchFeeding
        fields = ['batchFeedingID', 'batchID', 'feedingDate', 'feedingAmount', 'status']
        read_only_fields = ['batchFeedingID']
