"""
Breed Lifecycle API Views

Views for the breed configuration and guidance system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Sum, Count
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import json

from breeds.models import Breed, BreedType
from breeds.lifecycle_models import (
    BreedConfiguration, LifecycleStage, BreedGuideline, 
    FarmBreedPlan, GuidelineCompletion
)
from breeds.lifecycle_serializers import (
    BreedConfigurationSerializer, LifecycleStageSerializer,
    BreedGuidelineSerializer, FarmBreedPlanSerializer,
    FarmBreedPlanCreateSerializer, GuidelineCompletionSerializer,
    BreedRecommendationSerializer, BreedPerformanceAnalysisSerializer
)
from accounts.models import Farmer
from batches.models import Batch


class BreedConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for breed configurations - full CRUD for admins, read-only for farmers"""
    queryset = BreedConfiguration.objects.filter(is_active=True).select_related(
        'breed', 'breed__breed_typeID'
    ).prefetch_related('stages', 'guidelines')
    serializer_class = BreedConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Admin users can perform all actions, farmers can only read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'reset_to_default', 'bulk_configure']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by breed type if specified
        breed_type = self.request.query_params.get('breed_type')
        if breed_type:
            queryset = queryset.filter(breed__breed_typeID__breedType__icontains=breed_type)
        
        # Filter by purpose
        purpose = self.request.query_params.get('purpose')
        if purpose:
            queryset = queryset.filter(purpose=purpose)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def recommend_breed(self, request):
        """Recommend breeds based on farmer preferences"""
        serializer = BreedRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Logic for breed recommendation
            recommendations = []
            configs = self.get_queryset()
            
            # Filter by primary goal
            if data['primary_goal'] == 'EGGS':
                configs = configs.filter(purpose='LAYERS')
            elif data['primary_goal'] == 'MEAT':
                configs = configs.filter(purpose='BROILERS')
            
            # Add recommendations based on experience level and budget
            for config in configs[:3]:  # Limit to top 3 recommendations
                recommendation = {
                    'configuration': BreedConfigurationSerializer(config).data,
                    'suitability_score': self._calculate_suitability_score(config, data),
                    'estimated_roi': self._calculate_estimated_roi(config, data),
                    'difficulty_level': self._get_difficulty_level(config),
                    'initial_investment': self._estimate_initial_investment(config, data)
                }
                recommendations.append(recommendation)
            
            # Sort by suitability score
            recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return Response({
                'recommendations': recommendations,
                'farmer_profile': data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def reset_to_default(self, request, pk=None):
        """Reset breed configuration to default values"""
        config = self.get_object()
        breed_name = config.breed.breedName.lower()
        
        try:
            with transaction.atomic():
                # Reset configuration based on breed type
                if 'rhode island red' in breed_name or config.purpose == 'EGGS':
                    # Reset to egg chicken defaults
                    config.purpose = 'EGGS'
                    config.brooding_end_week = 6
                    config.growing_end_week = 16
                    config.laying_start_week = 17
                    config.expected_laying_rate = 85.0
                    config.optimal_temperature_min = 18.0
                    config.optimal_temperature_max = 24.0
                    config.optimal_humidity_min = 60.0
                    config.optimal_humidity_max = 70.0
                elif 'cobb' in breed_name or config.purpose == 'MEAT':
                    # Reset to meat chicken defaults
                    config.purpose = 'MEAT'
                    config.brooding_end_week = 3
                    config.growing_end_week = 6
                    config.slaughter_week = 8
                    config.target_weight_at_slaughter = 2500.0
                    config.optimal_temperature_min = 20.0
                    config.optimal_temperature_max = 26.0
                    config.optimal_humidity_min = 50.0
                    config.optimal_humidity_max = 65.0
                
                config.save()
                
                # Reset lifecycle stages to defaults
                LifecycleStage.objects.filter(breed_config=config).delete()
                self._create_default_stages(config)
                
                # Reset guidelines to defaults
                BreedGuideline.objects.filter(breed_config=config).delete()
                self._create_default_guidelines(config)
                
            serializer = self.get_serializer(config)
            return Response({
                'message': f'Breed configuration for {config.breed.breedName} reset to defaults',
                'configuration': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to reset configuration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def bulk_configure(self, request):
        """Bulk configure multiple breed configurations"""
        configurations = request.data.get('configurations', [])
        updated_configs = []
        errors = []
        
        try:
            with transaction.atomic():
                for config_data in configurations:
                    try:
                        config_id = config_data.get('configuration_id')
                        config = BreedConfiguration.objects.get(configuration_id=config_id)
                        
                        # Update configuration fields
                        for field, value in config_data.items():
                            if hasattr(config, field) and field != 'configuration_id':
                                setattr(config, field, value)
                        
                        config.save()
                        updated_configs.append(config.configuration_id)
                        
                    except BreedConfiguration.DoesNotExist:
                        errors.append(f"Configuration {config_id} not found")
                    except Exception as e:
                        errors.append(f"Failed to update configuration {config_id}: {str(e)}")
                
            return Response({
                'message': f'Successfully updated {len(updated_configs)} configurations',
                'updated_configurations': updated_configs,
                'errors': errors
            })
            
        except Exception as e:
            return Response({
                'error': f'Bulk configuration failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def export_configuration(self, request, pk=None):
        """Export breed configuration as JSON for backup/sharing"""
        config = self.get_object()
        
        export_data = {
            'breed_configuration': BreedConfigurationSerializer(config).data,
            'lifecycle_stages': LifecycleStageSerializer(config.stages.all(), many=True).data,
            'breed_guidelines': BreedGuidelineSerializer(config.guidelines.all(), many=True).data,
            'export_timestamp': timezone.now().isoformat(),
            'exported_by': request.user.username
        }
        
        return Response({
            'export_data': export_data,
            'filename': f'{config.breed.breedName}_configuration_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def import_configuration(self, request):
        """Import breed configuration from JSON"""
        import_data = request.data.get('import_data')
        
        if not import_data:
            return Response({
                'error': 'No import data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Import breed configuration
                config_data = import_data.get('breed_configuration', {})
                breed_id = config_data.get('breed')
                
                if not breed_id:
                    return Response({
                        'error': 'Breed ID is required in configuration data'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                breed = Breed.objects.get(breedID=breed_id)
                config, created = BreedConfiguration.objects.get_or_create(
                    breed=breed,
                    defaults=config_data
                )
                
                if not created:
                    # Update existing configuration
                    for field, value in config_data.items():
                        if hasattr(config, field) and field not in ['configuration_id', 'breed']:
                            setattr(config, field, value)
                    config.save()
                
                # Import lifecycle stages
                stages_data = import_data.get('lifecycle_stages', [])
                LifecycleStage.objects.filter(breed_config=config).delete()
                
                for stage_data in stages_data:
                    stage_data['breed_config'] = config.configuration_id
                    stage_data.pop('stage_id', None)  # Remove old ID
                    LifecycleStage.objects.create(**stage_data)
                
                # Import guidelines
                guidelines_data = import_data.get('breed_guidelines', [])
                BreedGuideline.objects.filter(breed_config=config).delete()
                
                for guideline_data in guidelines_data:
                    guideline_data['breed_config'] = config.configuration_id
                    guideline_data.pop('guideline_id', None)  # Remove old ID
                    
                    # Handle stage reference
                    stage_name = guideline_data.pop('stage_name', None)
                    if stage_name:
                        try:
                            stage = LifecycleStage.objects.get(
                                breed_config=config,
                                stage_name=stage_name
                            )
                            guideline_data['stage'] = stage.stage_id
                        except LifecycleStage.DoesNotExist:
                            guideline_data['stage'] = None
                    
                    BreedGuideline.objects.create(**guideline_data)
                
            return Response({
                'message': f'Successfully imported configuration for {breed.breedName}',
                'configuration_id': config.configuration_id,
                'action': 'created' if created else 'updated'
            })
            
        except Breed.DoesNotExist:
            return Response({
                'error': 'Breed not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Import failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_default_stages(self, config):
        """Create default lifecycle stages based on breed purpose"""
        if config.purpose == 'EGGS':
            # Egg chicken stages
            stages = [
                {
                    'stage_name': 'BROODING',
                    'start_week': 0, 'end_week': 6,
                    'daily_feed_per_bird': 25.0, 'feeding_frequency': 4,
                    'water_requirement': 50.0, 'temperature_min': 32.0, 'temperature_max': 35.0,
                    'humidity_min': 60.0, 'humidity_max': 65.0, 'floor_space_per_bird': 0.5,
                    'critical_monitoring_points': '["Temperature control", "Water access", "Feed intake", "Behavior observation"]',
                    'common_health_issues': '["Pasty butt", "Respiratory issues", "Dehydration", "Hypothermia"]'
                },
                {
                    'stage_name': 'GROWING',
                    'start_week': 7, 'end_week': 16,
                    'daily_feed_per_bird': 80.0, 'feeding_frequency': 3,
                    'water_requirement': 200.0, 'temperature_min': 18.0, 'temperature_max': 24.0,
                    'humidity_min': 60.0, 'humidity_max': 70.0, 'floor_space_per_bird': 1.0,
                    'critical_monitoring_points': '["Weight gain", "Feather development", "Feed conversion", "Social behavior"]',
                    'common_health_issues': '["Coccidiosis", "Respiratory infections", "Cannibalism", "Nutritional deficiencies"]'
                },
                {
                    'stage_name': 'LAYING',
                    'start_week': 17, 'end_week': 72,
                    'daily_feed_per_bird': 120.0, 'feeding_frequency': 2,
                    'water_requirement': 300.0, 'temperature_min': 18.0, 'temperature_max': 24.0,
                    'humidity_min': 60.0, 'humidity_max': 70.0, 'floor_space_per_bird': 1.5,
                    'critical_monitoring_points': '["Egg production rate", "Egg quality", "Feed intake", "Calcium levels", "Nest box usage"]',
                    'common_health_issues': '["Egg binding", "Prolapse", "Calcium deficiency", "Fatty liver syndrome", "Respiratory issues"]'
                }
            ]
        else:  # MEAT
            # Meat chicken stages
            stages = [
                {
                    'stage_name': 'BROODING',
                    'start_week': 0, 'end_week': 3,
                    'daily_feed_per_bird': 30.0, 'feeding_frequency': 4,
                    'water_requirement': 60.0, 'temperature_min': 32.0, 'temperature_max': 35.0,
                    'humidity_min': 50.0, 'humidity_max': 65.0, 'floor_space_per_bird': 0.5,
                    'critical_monitoring_points': '["Temperature control", "Water access", "Feed intake", "Growth rate"]',
                    'common_health_issues': '["Sudden death syndrome", "Ascites", "Leg problems", "Respiratory issues"]'
                },
                {
                    'stage_name': 'GROWING',
                    'start_week': 4, 'end_week': 6,
                    'daily_feed_per_bird': 150.0, 'feeding_frequency': 3,
                    'water_requirement': 300.0, 'temperature_min': 20.0, 'temperature_max': 26.0,
                    'humidity_min': 50.0, 'humidity_max': 65.0, 'floor_space_per_bird': 1.0,
                    'critical_monitoring_points': '["Weight gain", "Feed conversion", "Leg health", "Heart health"]',
                    'common_health_issues': '["Leg weakness", "Heart failure", "Heat stress", "Feed conversion issues"]'
                },
                {
                    'stage_name': 'FINISHING',
                    'start_week': 7, 'end_week': 8,
                    'daily_feed_per_bird': 180.0, 'feeding_frequency': 2,
                    'water_requirement': 400.0, 'temperature_min': 18.0, 'temperature_max': 24.0,
                    'humidity_min': 50.0, 'humidity_max': 65.0, 'floor_space_per_bird': 1.5,
                    'critical_monitoring_points': '["Final weight gain", "Feed withdrawal", "Processing preparation", "Stress minimization"]',
                    'common_health_issues': '["Ascites", "Sudden death", "Leg disorders", "Heat stress"]'
                }
            ]
        
        for stage_data in stages:
            LifecycleStage.objects.create(breed_config=config, **stage_data)
    
    def _create_default_guidelines(self, config):
        """Create default guidelines based on breed purpose"""
        if config.purpose == 'EGGS':
            guidelines = [
                {
                    'guideline_type': 'FEEDING',
                    'title': 'Brooding Stage Feeding Protocol',
                    'description': 'Critical feeding requirements during the first 6 weeks of life',
                    'applicable_from_week': 0, 'applicable_to_week': 6,
                    'priority': 'HIGH', 'is_critical': True,
                    'implementation_steps': '["Provide 24% protein starter feed", "Ensure feed is always available", "Use crumbles for easy consumption", "Monitor feed intake daily", "Provide fresh water 24/7"]',
                    'required_resources': '["Chick starter feed (24% protein)", "Feeder troughs", "Water dispensers", "Feed storage containers"]',
                    'success_indicators': '["Steady weight gain", "Active feeding behavior", "Good feather development", "Low mortality rate"]'
                },
                {
                    'guideline_type': 'HEALTH',
                    'title': 'Laying Stage Health Monitoring',
                    'description': 'Essential health monitoring during peak egg production',
                    'applicable_from_week': 17, 'applicable_to_week': 72,
                    'priority': 'HIGH', 'is_critical': True,
                    'implementation_steps': '["Daily egg collection and quality check", "Monitor calcium intake", "Check for egg binding symptoms", "Weekly weight monitoring", "Observe laying behavior"]',
                    'required_resources': '["Calcium supplements", "Nest boxes", "Scale for weighing", "Health monitoring checklist"]',
                    'success_indicators': '["Consistent egg production", "Good egg quality", "No laying problems", "Healthy body weight"]'
                }
            ]
        else:  # MEAT
            guidelines = [
                {
                    'guideline_type': 'ENVIRONMENT',
                    'title': 'Growth Stage Environment Control',
                    'description': 'Optimal environmental conditions for rapid growth phase',
                    'applicable_from_week': 4, 'applicable_to_week': 6,
                    'priority': 'HIGH', 'is_critical': True,
                    'implementation_steps': '["Maintain temperature 20-26°C", "Ensure proper ventilation", "Monitor humidity 50-65%", "Provide adequate floor space", "Check for heat stress signs"]',
                    'required_resources': '["Temperature monitors", "Ventilation system", "Humidity gauges", "Cooling systems"]',
                    'success_indicators': '["Optimal growth rate", "No heat stress", "Good feed conversion", "Active behavior"]'
                }
            ]
        
        for guideline_data in guidelines:
            BreedGuideline.objects.create(breed_config=config, **guideline_data)
    
    def _calculate_suitability_score(self, config, farmer_data):
        """Calculate suitability score based on farmer profile"""
        score = 50  # Base score
        
        # Adjust based on experience level
        if farmer_data['experience_level'] == 'BEGINNER':
            if config.purpose == 'LAYERS':
                score += 20  # Layers are generally easier
            else:
                score += 10
        elif farmer_data['experience_level'] == 'ADVANCED':
            score += 30
        
        # Adjust based on budget
        if farmer_data['budget_range'] == 'HIGH':
            score += 20
        elif farmer_data['budget_range'] == 'LOW' and config.purpose == 'LAYERS':
            score += 10  # Lower initial investment for layers
        
        return min(score, 100)
    
    def _calculate_estimated_roi(self, config, farmer_data):
        """Calculate estimated ROI percentage"""
        # This is a simplified calculation - in practice, you'd use market data
        if config.purpose == 'LAYERS':
            return 35.0  # 35% annual ROI for layers
        else:
            return 25.0  # 25% per cycle for broilers
    
    def _get_difficulty_level(self, config):
        """Get difficulty level for the breed"""
        if config.purpose == 'LAYERS':
            return 'Medium'
        else:
            return 'Easy'
    
    def _estimate_initial_investment(self, config, farmer_data):
        """Estimate initial investment required"""
        # Simplified calculation based on purpose and farm size
        base_cost = 50000 if config.purpose == 'LAYERS' else 30000  # Base cost in local currency
        
        if farmer_data['farm_size'] == 'LARGE':
            return base_cost * 3
        elif farmer_data['farm_size'] == 'MEDIUM':
            return base_cost * 2
        else:
            return base_cost


class FarmBreedPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for farm breed plans"""
    queryset = FarmBreedPlan.objects.all().select_related(
        'farmer', 'batch', 'breed_config__breed'
    ).prefetch_related('completions__guideline')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FarmBreedPlanCreateSerializer
        return FarmBreedPlanSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by farmer if user is a farmer
        user = self.request.user
        if hasattr(user, 'farmer'):
            queryset = queryset.filter(farmer=user.farmer)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by breed purpose
        purpose = self.request.query_params.get('purpose')
        if purpose:
            queryset = queryset.filter(breed_config__purpose=purpose)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def current_guidelines(self, request, pk=None):
        """Get current applicable guidelines for a breed plan"""
        plan = self.get_object()
        current_age = plan.current_age_weeks
        
        guidelines = BreedGuideline.objects.filter(
            breed_config=plan.breed_config,
            applicable_from_week__lte=current_age,
            applicable_to_week__gte=current_age,
            is_active=True
        ).order_by('priority', 'guideline_type')
        
        serializer = BreedGuidelineSerializer(guidelines, many=True)
        return Response({
            'current_age_weeks': current_age,
            'current_stage': plan.get_current_stage_display(),
            'guidelines': serializer.data,
            'total_guidelines': guidelines.count(),
            'critical_guidelines': guidelines.filter(is_critical=True).count()
        })
    
    @action(detail=True, methods=['post'])
    def complete_guideline(self, request, pk=None):
        """Mark a guideline as completed"""
        plan = self.get_object()
        guideline_id = request.data.get('guideline_id')
        completion_notes = request.data.get('completion_notes', '')
        success_rating = request.data.get('success_rating', 5)
        measured_results = request.data.get('measured_results', {})
        farmer_feedback = request.data.get('farmer_feedback', '')
        
        try:
            guideline = BreedGuideline.objects.get(
                guideline_id=guideline_id,
                breed_config=plan.breed_config
            )
            
            completion, created = GuidelineCompletion.objects.get_or_create(
                plan=plan,
                guideline=guideline,
                defaults={
                    'completion_notes': completion_notes,
                    'success_rating': success_rating,
                    'measured_results': measured_results,
                    'farmer_feedback': farmer_feedback
                }
            )
            
            if not created:
                # Update existing completion
                completion.completion_notes = completion_notes
                completion.success_rating = success_rating
                completion.measured_results = measured_results
                completion.farmer_feedback = farmer_feedback
                completion.completed_at = timezone.now()
                completion.save()
            
            serializer = GuidelineCompletionSerializer(completion)
            return Response({
                'message': 'Guideline completed successfully',
                'completion': serializer.data
            })
        
        except BreedGuideline.DoesNotExist:
            return Response(
                {'error': 'Guideline not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_metrics(self, request, pk=None):
        """Update plan metrics (bird count, feed consumption, etc.)"""
        plan = self.get_object()
        
        # Update metrics from request data
        if 'current_bird_count' in request.data:
            plan.current_bird_count = request.data['current_bird_count']
        
        if 'mortality_count' in request.data:
            plan.mortality_count = request.data['mortality_count']
        
        if 'actual_feed_consumption' in request.data:
            plan.actual_feed_consumption = request.data['actual_feed_consumption']
        
        if 'total_eggs_collected' in request.data:
            plan.total_eggs_collected = request.data['total_eggs_collected']
        
        if 'health_issues_count' in request.data:
            plan.health_issues_count = request.data['health_issues_count']
        
        # Update current age and stage
        if 'current_age_weeks' in request.data:
            plan.current_age_weeks = request.data['current_age_weeks']
            plan.current_stage = plan.breed_config.get_current_stage(plan.current_age_weeks)
        
        # Calculate current laying rate for layers
        if plan.breed_config.purpose == 'LAYERS' and plan.current_bird_count > 0:
            # This would typically be calculated over a period (e.g., weekly)
            eggs_per_day = request.data.get('daily_eggs_collected', 0)
            plan.current_laying_rate = (eggs_per_day / plan.current_bird_count) * 100
        
        plan.save()
        
        serializer = self.get_serializer(plan)
        return Response({
            'message': 'Metrics updated successfully',
            'plan': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def performance_analysis(self, request, pk=None):
        """Get performance analysis for a breed plan"""
        plan = self.get_object()
        
        analysis = {
            'plan_summary': {
                'age_weeks': plan.current_age_weeks,
                'initial_birds': plan.initial_bird_count,
                'current_birds': plan.current_bird_count,
                'mortality_rate': round((plan.mortality_count / plan.initial_bird_count) * 100, 2) if plan.initial_bird_count > 0 else 0,
                'feed_consumption_kg': float(plan.actual_feed_consumption or 0),
                'total_eggs': plan.total_eggs_collected or 0,
                'health_issues': plan.health_issues_count or 0
            },
            'performance_indicators': self._calculate_performance_indicators(plan),
            'guideline_completion': self._calculate_guideline_completion(plan),
            'recommendations': self._generate_recommendations(plan)
        }
        
        return Response(analysis)
    
    def _calculate_performance_indicators(self, plan):
        """Calculate key performance indicators"""
        indicators = {}
        
        # Mortality rate
        if plan.initial_bird_count > 0:
            mortality_rate = (plan.mortality_count / plan.initial_bird_count) * 100
            indicators['mortality_rate'] = {
                'value': round(mortality_rate, 2),
                'status': 'good' if mortality_rate < 5 else 'warning' if mortality_rate < 10 else 'critical',
                'benchmark': 5.0
            }
        
        # Feed conversion ratio (simplified)
        if plan.current_bird_count > 0 and plan.actual_feed_consumption:
            # This is a simplified calculation
            estimated_weight = plan.current_bird_count * 2  # Placeholder
            fcr = float(plan.actual_feed_consumption) / estimated_weight if estimated_weight > 0 else 0
            indicators['feed_conversion_ratio'] = {
                'value': round(fcr, 2),
                'status': 'good' if fcr < 2.0 else 'warning' if fcr < 2.5 else 'critical',
                'benchmark': 2.0
            }
        
        # Egg production rate (for layers)
        if plan.breed_config.purpose == 'LAYERS' and plan.current_laying_rate:
            indicators['laying_rate'] = {
                'value': round(plan.current_laying_rate, 2),
                'status': 'good' if plan.current_laying_rate > 80 else 'warning' if plan.current_laying_rate > 60 else 'critical',
                'benchmark': 85.0
            }
        
        return indicators
    
    def _calculate_guideline_completion(self, plan):
        """Calculate guideline completion statistics"""
        total_guidelines = BreedGuideline.objects.filter(
            breed_config=plan.breed_config,
            applicable_from_week__lte=plan.current_age_weeks,
            is_active=True
        ).count()
        
        completed_guidelines = GuidelineCompletion.objects.filter(plan=plan).count()
        
        completion_rate = (completed_guidelines / total_guidelines * 100) if total_guidelines > 0 else 0
        
        return {
            'total_applicable': total_guidelines,
            'completed': completed_guidelines,
            'completion_rate': round(completion_rate, 2),
            'status': 'good' if completion_rate > 80 else 'warning' if completion_rate > 60 else 'critical'
        }
    
    def _generate_recommendations(self, plan):
        """Generate recommendations based on performance"""
        recommendations = []
        
        # Check mortality rate
        if plan.initial_bird_count > 0:
            mortality_rate = (plan.mortality_count / plan.initial_bird_count) * 100
            if mortality_rate > 10:
                recommendations.append({
                    'type': 'critical',
                    'category': 'Health Management',
                    'message': 'High mortality rate detected. Review biosecurity measures and consult veterinarian.',
                    'action': 'immediate'
                })
            elif mortality_rate > 5:
                recommendations.append({
                    'type': 'warning',
                    'category': 'Health Management',
                    'message': 'Mortality rate is above optimal. Monitor health conditions closely.',
                    'action': 'monitor'
                })
        
        # Check feed conversion
        if plan.actual_feed_consumption and plan.current_bird_count > 0:
            # Simplified FCR check
            daily_feed_per_bird = float(plan.actual_feed_consumption) / (plan.current_bird_count * plan.current_age_weeks * 7)
            if daily_feed_per_bird > 150:  # grams per day
                recommendations.append({
                    'type': 'info',
                    'category': 'Feed Management',
                    'message': 'Feed consumption is higher than expected. Review feed quality and feeding schedule.',
                    'action': 'optimize'
                })
        
        # Check guideline completion
        completion_stats = self._calculate_guideline_completion(plan)
        if completion_stats['completion_rate'] < 60:
            recommendations.append({
                'type': 'warning',
                'category': 'Management Practices',
                'message': 'Low guideline completion rate. Following guidelines improves performance.',
                'action': 'improve'
            })
        
        return recommendations
