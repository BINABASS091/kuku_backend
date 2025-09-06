from rest_framework import serializers
from breeds.models import (
    BreedType, Breed, ActivityType, BreedActivity, 
    ConditionType, BreedCondition, FoodType, BreedFeeding, BreedGrowth
)

class BreedTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreedType
        fields = '__all__'

class BreedSerializer(serializers.ModelSerializer):
    # Accept FK by id on write
    type = serializers.PrimaryKeyRelatedField(queryset=BreedType.objects.all())
    # Provide nested details on read
    type_detail = BreedTypeSerializer(source='type', read_only=True)

    class Meta:
        model = Breed
        fields = ['id', 'name', 'type', 'type_detail', 'photo']

class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = '__all__'

class BreedActivitySerializer(serializers.ModelSerializer):
    # Write as PKs
    breed = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    activity_type = serializers.PrimaryKeyRelatedField(queryset=ActivityType.objects.all())
    # Read details
    breed_detail = BreedSerializer(source='breed', read_only=True)
    activity_type_detail = ActivityTypeSerializer(source='activity_type', read_only=True)
    
    class Meta:
        model = BreedActivity
        fields = ['id', 'breed', 'breed_detail', 'activity_type', 'activity_type_detail', 'age', 'status']

class ConditionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionType
        fields = '__all__'

class BreedConditionSerializer(serializers.ModelSerializer):
    # Write as PKs
    breed = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    condition_type = serializers.PrimaryKeyRelatedField(queryset=ConditionType.objects.all())
    # Read details
    breed_detail = BreedSerializer(source='breed', read_only=True)
    condition_type_detail = ConditionTypeSerializer(source='condition_type', read_only=True)
    
    class Meta:
        model = BreedCondition
        fields = ['id', 'breed', 'breed_detail', 'condition_type', 'condition_type_detail', 'min_value', 'max_value', 'status']

class FoodTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodType
        fields = '__all__'

class BreedFeedingSerializer(serializers.ModelSerializer):
    # Write as PKs
    breed = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    food_type = serializers.PrimaryKeyRelatedField(queryset=FoodType.objects.all())
    # Read details
    breed_detail = BreedSerializer(source='breed', read_only=True)
    food_type_detail = FoodTypeSerializer(source='food_type', read_only=True)
    
    class Meta:
        model = BreedFeeding
        fields = ['id', 'breed', 'breed_detail', 'food_type', 'food_type_detail', 'age', 'quantity', 'frequency', 'status']

class BreedGrowthSerializer(serializers.ModelSerializer):
    # Write as PK
    breed = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all())
    # Read details
    breed_detail = BreedSerializer(source='breed', read_only=True)
    
    class Meta:
        model = BreedGrowth
        fields = ['id', 'breed', 'breed_detail', 'age', 'min_weight']
