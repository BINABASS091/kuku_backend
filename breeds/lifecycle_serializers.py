"""
Breed Lifecycle API Serializers

Serializers for the breed configuration and guidance system.
"""

from rest_framework import serializers
from breeds.models import Breed, BreedType
from breeds.lifecycle_models import (
    BreedConfiguration, LifecycleStage, BreedGuideline, 
    FarmBreedPlan, GuidelineCompletion
)
from accounts.models import Farmer
from batches.models import Batch
import json


class LifecycleStageSerializer(serializers.ModelSerializer):
    stage_name_display = serializers.CharField(source='get_stage_name_display', read_only=True)
    critical_monitoring_points = serializers.JSONField()
    common_health_issues = serializers.JSONField()
    
    class Meta:
        model = LifecycleStage
        fields = [
            'stage_id', 'stage_name', 'stage_name_display', 'start_week', 'end_week',
            'daily_feed_per_bird', 'feeding_frequency', 'water_requirement',
            'temperature_min', 'temperature_max', 'humidity_min', 'humidity_max',
            'floor_space_per_bird', 'critical_monitoring_points', 'common_health_issues'
        ]


class BreedGuidelineSerializer(serializers.ModelSerializer):
    guideline_type_display = serializers.CharField(source='get_guideline_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    implementation_steps = serializers.JSONField()
    required_resources = serializers.JSONField()
    success_indicators = serializers.JSONField()
    stage_name = serializers.CharField(source='stage.stage_name', read_only=True, allow_null=True)
    
    class Meta:
        model = BreedGuideline
        fields = [
            'guideline_id', 'guideline_type', 'guideline_type_display', 'title', 'description',
            'applicable_from_week', 'applicable_to_week', 'priority', 'priority_display',
            'is_critical', 'is_automated', 'implementation_steps', 'required_resources',
            'success_indicators', 'stage_name', 'is_active'
        ]


class BreedConfigurationSerializer(serializers.ModelSerializer):
    breed_name = serializers.CharField(source='breed.breedName', read_only=True)
    breed_type = serializers.CharField(source='breed.breed_typeID.breedType', read_only=True)
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)
    stages = LifecycleStageSerializer(many=True, read_only=True)
    guidelines = BreedGuidelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = BreedConfiguration
        fields = [
            'configuration_id', 'breed', 'breed_name', 'breed_type', 'purpose', 'purpose_display',
            'brooding_end_week', 'growing_end_week', 'laying_start_week', 'slaughter_week',
            'expected_laying_rate', 'target_weight_at_slaughter',
            'optimal_temperature_min', 'optimal_temperature_max',
            'optimal_humidity_min', 'optimal_humidity_max',
            'stages', 'guidelines', 'is_active', 'created_at', 'updated_at'
        ]


class GuidelineCompletionSerializer(serializers.ModelSerializer):
    guideline_title = serializers.CharField(source='guideline.title', read_only=True)
    guideline_type = serializers.CharField(source='guideline.guideline_type', read_only=True)
    measured_results = serializers.JSONField()
    
    class Meta:
        model = GuidelineCompletion
        fields = [
            'completion_id', 'guideline', 'guideline_title', 'guideline_type',
            'completed_at', 'completion_notes', 'success_rating',
            'measured_results', 'farmer_feedback'
        ]


class FarmBreedPlanSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.farmerName', read_only=True)
    breed_name = serializers.CharField(source='breed_config.breed.breedName', read_only=True)
    breed_purpose = serializers.CharField(source='breed_config.purpose', read_only=True)
    batch_name = serializers.CharField(source='batch.batchID', read_only=True)
    current_stage_display = serializers.CharField(source='get_current_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Performance metrics
    mortality_rate = serializers.SerializerMethodField()
    feed_conversion_ratio = serializers.SerializerMethodField()
    current_guidelines = BreedGuidelineSerializer(many=True, read_only=True)
    completions = GuidelineCompletionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FarmBreedPlan
        fields = [
            'plan_id', 'farmer', 'farmer_name', 'batch', 'batch_name',
            'breed_config', 'breed_name', 'breed_purpose',
            'start_date', 'planned_end_date', 'initial_bird_count', 'current_bird_count',
            'current_age_weeks', 'current_stage', 'current_stage_display',
            'actual_feed_consumption', 'mortality_count', 'health_issues_count',
            'total_eggs_collected', 'current_laying_rate',
            'status', 'status_display', 'mortality_rate', 'feed_conversion_ratio',
            'current_guidelines', 'completions', 'created_at', 'updated_at'
        ]
    
    def get_mortality_rate(self, obj):
        """Calculate mortality rate percentage"""
        if obj.initial_bird_count > 0:
            return round((obj.mortality_count / obj.initial_bird_count) * 100, 2)
        return 0.0
    
    def get_feed_conversion_ratio(self, obj):
        """Calculate feed conversion ratio"""
        if obj.current_bird_count > 0 and obj.actual_feed_consumption > 0:
            # This is a simplified calculation - in practice, you'd need weight gain data
            estimated_weight_gain = obj.current_bird_count * 100  # Placeholder calculation
            if estimated_weight_gain > 0:
                return round(float(obj.actual_feed_consumption) / estimated_weight_gain, 2)
        return 0.0


class FarmBreedPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmBreedPlan
        fields = [
            'farmer', 'batch', 'breed_config', 'start_date', 'planned_end_date',
            'initial_bird_count', 'current_bird_count', 'current_age_weeks'
        ]
    
    def create(self, validated_data):
        # Automatically set current_stage based on age and breed config
        breed_config = validated_data['breed_config']
        age_weeks = validated_data['current_age_weeks']
        validated_data['current_stage'] = breed_config.get_current_stage(age_weeks)
        return super().create(validated_data)


class BreedRecommendationSerializer(serializers.Serializer):
    """Serializer for breed recommendations based on farmer preferences"""
    farm_size = serializers.CharField()
    primary_goal = serializers.ChoiceField(choices=[
        ('EGGS', 'Egg Production'),
        ('MEAT', 'Meat Production'),
        ('BOTH', 'Both Eggs and Meat')
    ])
    experience_level = serializers.ChoiceField(choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ])
    budget_range = serializers.ChoiceField(choices=[
        ('LOW', 'Low Budget'),
        ('MEDIUM', 'Medium Budget'),
        ('HIGH', 'High Budget')
    ])
    
    def validate(self, data):
        """Add any cross-field validation here"""
        return data


class BreedPerformanceAnalysisSerializer(serializers.Serializer):
    """Serializer for breed performance analysis"""
    plan_id = serializers.IntegerField()
    analysis_period = serializers.ChoiceField(choices=[
        ('WEEK', 'Weekly'),
        ('MONTH', 'Monthly'),
        ('LIFECYCLE', 'Full Lifecycle')
    ])
    metrics = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('GROWTH', 'Growth Rate'),
            ('FEED_CONVERSION', 'Feed Conversion'),
            ('MORTALITY', 'Mortality Rate'),
            ('PRODUCTION', 'Production Rate'),
            ('HEALTH', 'Health Score')
        ]),
        allow_empty=False
    )
