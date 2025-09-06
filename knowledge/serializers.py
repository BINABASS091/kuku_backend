from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from knowledge.models import (
    PatientHealth, Recommendation, ExceptionDisease, 
    Anomaly, Medication
)
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with basic information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']


class PatientHealthSerializer(serializers.ModelSerializer):
    """
    Serializer for PatientHealth model with validation.
    """
    class Meta:
        model = PatientHealth
        fields = ['id', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_description(self, value):
        if not value or not value.strip():
            raise ValidationError(_("Description cannot be empty."))
        if len(value) > 100:
            raise ValidationError(_("Description is too long (max 100 characters)."))
        return value.strip()


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for Recommendation model with validation.
    """
    class Meta:
        model = Recommendation
        fields = [
            'id', 'description', 'reco_type', 'context', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate recommendation data.
        """
        # Validate description
        description = data.get('description', '').strip()
        if not description:
            raise ValidationError({"description": _("Description cannot be empty.")})
        
        # Validate reco_type
        reco_type = data.get('reco_type')
        if reco_type not in dict(Recommendation.RECO_TYPE_CHOICES):
            raise ValidationError({
                "reco_type": _("Invalid recommendation type.")
            })
            
        # Validate context
        context = data.get('context')
        if context not in dict(Recommendation.CONTEXT_CHOICES):
            raise ValidationError({
                "context": _("Invalid context value.")
            })
            
        return data


class ExceptionDiseaseSerializer(serializers.ModelSerializer):
    """
    Serializer for ExceptionDisease model with validation.
    """
    recommendation = RecommendationSerializer(read_only=True)
    recommendation_id = serializers.PrimaryKeyRelatedField(
        queryset=Recommendation.objects.all(),
        source='recommendation',
        write_only=True,
        required=True
    )
    
    patient_health = PatientHealthSerializer(read_only=True)
    patient_health_id = serializers.PrimaryKeyRelatedField(
        queryset=PatientHealth.objects.all(),
        source='patient_health',
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ExceptionDisease
        fields = [
            'id', 'recommendation', 'recommendation_id', 
            'patient_health', 'patient_health_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate exception disease data.
        """
        # Check if the exception already exists
        recommendation = data.get('recommendation')
        patient_health = data.get('patient_health')
        
        if self.instance is None:  # Only check on creation
            if ExceptionDisease.objects.filter(
                recommendation=recommendation,
                patient_health=patient_health
            ).exists():
                raise ValidationError({
                    "detail": _("This exception already exists.")
                })
                
        return data


class AnomalySerializer(serializers.ModelSerializer):
    """
    Serializer for Anomaly model with validation.
    """
    class Meta:
        model = Anomaly
        fields = [
            'id', 'hr_id', 'sp_id', 'pr_id', 'bt_id', 'resp_id',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate anomaly data.
        """
        # Ensure all IDs are positive integers
        for field in ['hr_id', 'sp_id', 'pr_id', 'bt_id', 'resp_id']:
            if field in data and data[field] < 0:
                raise ValidationError({
                    field: _("ID must be a positive integer.")
                })
                
        return data


class MedicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Medication model with validation.
    """
    anomaly = AnomalySerializer(read_only=True)
    anomaly_id = serializers.PrimaryKeyRelatedField(
        queryset=Anomaly.objects.all(),
        source='anomaly',
        write_only=True,
        required=True
    )
    
    recommendation = RecommendationSerializer(read_only=True)
    recommendation_id = serializers.PrimaryKeyRelatedField(
        queryset=Recommendation.objects.all(),
        source='recommendation',
        write_only=True,
        required=True
    )
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Medication
        fields = [
            'id', 'anomaly', 'anomaly_id', 'recommendation', 'recommendation_id',
            'user', 'sequence_no', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_sequence_no(self, value):
        """
        Validate sequence number.
        """
        if value < 1:
            raise ValidationError(_("Sequence number must be at least 1."))
        return value
    
    def validate(self, data):
        """
        Validate medication data.
        """
        # Check for duplicate sequence numbers for the same anomaly
        anomaly = data.get('anomaly') or getattr(self.instance, 'anomaly', None)
        sequence_no = data.get('sequence_no')
        
        if anomaly and sequence_no:
            qs = Medication.objects.filter(
                anomaly=anomaly,
                sequence_no=sequence_no
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise ValidationError({
                    "sequence_no": _("A medication with this sequence number already exists for this anomaly.")
                })
                
        return data
    
    def create(self, validated_data):
        """
        Create a new medication with the current user as the creator.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
