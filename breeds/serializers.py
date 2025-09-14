from rest_framework import serializers
from breeds.models import (
    BreedType, Breed, ActivityType, BreedActivity, 
    ConditionType, BreedCondition, FoodType, BreedFeeding, BreedGrowth
)

class BreedTypeSerializer(serializers.ModelSerializer):
    breeds_count = serializers.SerializerMethodField()
    total_activities = serializers.SerializerMethodField()
    
    class Meta:
        model = BreedType
        fields = ['breed_typeID', 'breedType', 'breeds_count', 'total_activities']
    
    def get_breeds_count(self, obj):
        """Get total number of breeds for this breed type"""
        return obj.breeds.count()
    
    def get_total_activities(self, obj):
        """Get total activities across all breeds of this type"""
        total = 0
        for breed in obj.breeds.all():
            total += breed.breed_activities.count()
        return total

class BreedSerializer(serializers.ModelSerializer):
    breed_typeID = serializers.PrimaryKeyRelatedField(queryset=BreedType.objects.all())
    type_detail = BreedTypeSerializer(source='breed_typeID', read_only=True)
    activities_count = serializers.SerializerMethodField()
    conditions_count = serializers.SerializerMethodField()
    feeding_schedules_count = serializers.SerializerMethodField()
    growth_records_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Breed
        fields = ['breedID', 'breedName', 'breed_typeID', 'type_detail', 'preedphoto', 
                 'activities_count', 'conditions_count', 'feeding_schedules_count', 'growth_records_count']
    
    def get_activities_count(self, obj):
        """Get number of activities for this breed"""
        return obj.breed_activities.count()
    
    def get_conditions_count(self, obj):
        """Get number of health conditions for this breed"""
        return obj.breed_conditions.count()
    
    def get_feeding_schedules_count(self, obj):
        """Get number of feeding schedules for this breed"""
        return obj.breed_feeding_rules.count()
    
    def get_growth_records_count(self, obj):
        """Get number of growth records for this breed"""
        return obj.breed_growth.count()

class ActivityTypeSerializer(serializers.ModelSerializer):
    total_breed_activities = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityType
        fields = ['activityTypeID', 'activityType', 'total_breed_activities']
    
    def get_total_breed_activities(self, obj):
        """Get total breed activities using this activity type"""
        return obj.breed_activity_types.count()

class BreedActivitySerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    activityTypeID = serializers.PrimaryKeyRelatedField(queryset=ActivityType.objects.all(), source='activityTypeID')
    breed_detail = BreedSerializer(source='breedID', read_only=True)
    activity_type_detail = ActivityTypeSerializer(source='activityTypeID', read_only=True)

    class Meta:
        model = BreedActivity
        fields = ['breedActivityID', 'breedID', 'breed_detail', 'activityTypeID', 'activity_type_detail', 'age', 'breed_activity_status']

class ConditionTypeSerializer(serializers.ModelSerializer):
    breed_conditions_count = serializers.SerializerMethodField()
    active_conditions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConditionType
        fields = ['condition_typeID', 'name', 'breed_conditions_count', 'active_conditions_count']
    
    def get_breed_conditions_count(self, obj):
        """Get total breed conditions using this condition type"""
        return obj.breed_condition_types.count()
    
    def get_active_conditions_count(self, obj):
        """Get active breed conditions for this type"""
        return obj.breed_condition_types.filter(condition_status=1).count()

class BreedConditionSerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    condition_typeID = serializers.PrimaryKeyRelatedField(queryset=ConditionType.objects.all(), source='condition_typeID')
    breed_detail = BreedSerializer(source='breedID', read_only=True)
    condition_type_detail = ConditionTypeSerializer(source='condition_typeID', read_only=True)
    condition_range = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = BreedCondition
        fields = ['breed_conditionID', 'breedID', 'breed_detail', 'condition_typeID', 'condition_type_detail', 
                 'condictionMin', 'conditionMax', 'condition_status', 'condition_range', 'status_display']
    
    def get_condition_range(self, obj):
        """Get formatted condition range"""
        return f"{obj.condictionMin} - {obj.conditionMax}"
    
    def get_status_display(self, obj):
        """Get human readable status"""
        return "Active" if obj.condition_status == 1 else "Inactive"

class FoodTypeSerializer(serializers.ModelSerializer):
    feeding_schedules_count = serializers.SerializerMethodField()
    breeds_using_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodType
        fields = ['foodTypeID', 'name', 'feeding_schedules_count', 'breeds_using_count']
    
    def get_feeding_schedules_count(self, obj):
        """Get total feeding schedules using this food type"""
        return obj.breed_feeding_types.count()
    
    def get_breeds_using_count(self, obj):
        """Get unique breeds using this food type"""
        return obj.breed_feeding_types.values('breedID').distinct().count()

class BreedFeedingSerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    foodTypeID = serializers.PrimaryKeyRelatedField(queryset=FoodType.objects.all(), source='foodTypeID')
    breed_detail = BreedSerializer(source='breedID', read_only=True)
    food_type_detail = FoodTypeSerializer(source='foodTypeID', read_only=True)

    class Meta:
        model = BreedFeeding
        fields = ['breedFeedingID', 'breedID', 'breed_detail', 'foodTypeID', 'food_type_detail', 'age', 'quantity', 'frequency', 'breed_feed_status']

class BreedGrowthSerializer(serializers.ModelSerializer):
    breedID = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.all(), source='breedID')
    breed_detail = BreedSerializer(source='breedID', read_only=True)

    class Meta:
        model = BreedGrowth
        fields = ['breedGrowthID', 'breedID', 'breed_detail', 'age', 'minWeight']
