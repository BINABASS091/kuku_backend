"""
Initial Breed Configurations for Egg and Meat Chickens

This file contains the setup data for the two initial breed types:
1. Egg Chicken (Layer)
2. Meat Chicken (Broiler)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from breeds.models import BreedType, Breed
from breeds.lifecycle_models import (
    BreedConfiguration, LifecycleStage, BreedGuideline
)
from decimal import Decimal
import json


class Command(BaseCommand):
    help = 'Create initial breed configurations for Egg and Meat chickens'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.create_breed_types()
            self.create_egg_chicken_config()
            self.create_meat_chicken_config()
            self.stdout.write(self.style.SUCCESS('Successfully created breed configurations'))

    def create_breed_types(self):
        """Create basic breed types and breeds"""
        # Create breed types
        layer_type, _ = BreedType.objects.get_or_create(
            breedType='Layer Chicken',
            defaults={'breed_typeID': 1}
        )
        broiler_type, _ = BreedType.objects.get_or_create(
            breedType='Broiler Chicken',
            defaults={'breed_typeID': 2}
        )
        
        # Create specific breeds
        self.layer_breed, _ = Breed.objects.get_or_create(
            breedName='Commercial Layer',
            defaults={
                'breed_typeID': layer_type,
                'preedphoto': 'layer_chicken.jpg'
            }
        )
        
        self.broiler_breed, _ = Breed.objects.get_or_create(
            breedName='Commercial Broiler',
            defaults={
                'breed_typeID': broiler_type,
                'preedphoto': 'broiler_chicken.jpg'
            }
        )

    def create_egg_chicken_config(self):
        """Create configuration for egg-laying chickens"""
        layer_config, _ = BreedConfiguration.objects.get_or_create(
            breed=self.layer_breed,
            defaults={
                'purpose': 'EGGS',
                'brooding_end_week': 6,
                'growing_end_week': 16,
                'laying_start_week': 17,
                'slaughter_week': None,  # Layers live longer
                'expected_laying_rate': Decimal('80.00'),
                'target_weight_at_slaughter': None,
                'optimal_temperature_min': Decimal('18.0'),
                'optimal_temperature_max': Decimal('25.0'),
                'optimal_humidity_min': Decimal('50.0'),
                'optimal_humidity_max': Decimal('70.0'),
            }
        )

        # Create lifecycle stages for layers
        stages_data = [
            {
                'stage_name': 'BROODING',
                'start_week': 0,
                'end_week': 6,
                'daily_feed_per_bird': Decimal('25.0'),
                'feeding_frequency': 4,
                'water_requirement': Decimal('50.0'),
                'temperature_min': Decimal('32.0'),  # Higher for chicks
                'temperature_max': Decimal('35.0'),
                'humidity_min': Decimal('60.0'),
                'humidity_max': Decimal('70.0'),
                'floor_space_per_bird': Decimal('0.5'),
                'critical_monitoring_points': json.dumps([
                    "Temperature regulation",
                    "Feed intake monitoring",
                    "Water consumption",
                    "Chick activity levels",
                    "Respiratory health"
                ]),
                'common_health_issues': json.dumps([
                    "Respiratory infections",
                    "Digestive problems",
                    "Temperature stress",
                    "Dehydration"
                ])
            },
            {
                'stage_name': 'GROWING',
                'start_week': 7,
                'end_week': 16,
                'daily_feed_per_bird': Decimal('85.0'),
                'feeding_frequency': 3,
                'water_requirement': Decimal('150.0'),
                'temperature_min': Decimal('18.0'),
                'temperature_max': Decimal('25.0'),
                'humidity_min': Decimal('50.0'),
                'humidity_max': Decimal('70.0'),
                'floor_space_per_bird': Decimal('1.0'),
                'critical_monitoring_points': json.dumps([
                    "Body weight development",
                    "Feather development",
                    "Feed conversion efficiency",
                    "Social behavior",
                    "Vaccination schedules"
                ]),
                'common_health_issues': json.dumps([
                    "Parasitic infections",
                    "Nutritional deficiencies",
                    "Leg problems",
                    "Feather pecking"
                ])
            },
            {
                'stage_name': 'LAYING',
                'start_week': 17,
                'end_week': 72,  # Typical laying period
                'daily_feed_per_bird': Decimal('120.0'),
                'feeding_frequency': 2,
                'water_requirement': Decimal('250.0'),
                'temperature_min': Decimal('18.0'),
                'temperature_max': Decimal('25.0'),
                'humidity_min': Decimal('50.0'),
                'humidity_max': Decimal('65.0'),
                'floor_space_per_bird': Decimal('1.5'),
                'critical_monitoring_points': json.dumps([
                    "Egg production rate",
                    "Egg quality",
                    "Feed consumption",
                    "Body weight maintenance",
                    "Nesting behavior"
                ]),
                'common_health_issues': json.dumps([
                    "Egg binding",
                    "Prolapse",
                    "Calcium deficiency",
                    "Reproductive disorders"
                ])
            }
        ]

        for stage_data in stages_data:
            LifecycleStage.objects.get_or_create(
                breed_config=layer_config,
                stage_name=stage_data['stage_name'],
                defaults=stage_data
            )

        # Create guidelines for layers
        self.create_layer_guidelines(layer_config)

    def create_meat_chicken_config(self):
        """Create configuration for meat chickens (broilers)"""
        broiler_config, _ = BreedConfiguration.objects.get_or_create(
            breed=self.broiler_breed,
            defaults={
                'purpose': 'MEAT',
                'brooding_end_week': 3,
                'growing_end_week': 6,
                'laying_start_week': None,  # Broilers don't lay
                'slaughter_week': 8,
                'expected_laying_rate': None,
                'target_weight_at_slaughter': Decimal('2500.00'),  # 2.5kg
                'optimal_temperature_min': Decimal('20.0'),
                'optimal_temperature_max': Decimal('25.0'),
                'optimal_humidity_min': Decimal('50.0'),
                'optimal_humidity_max': Decimal('65.0'),
            }
        )

        # Create lifecycle stages for broilers
        stages_data = [
            {
                'stage_name': 'BROODING',
                'start_week': 0,
                'end_week': 3,
                'daily_feed_per_bird': Decimal('30.0'),
                'feeding_frequency': 6,
                'water_requirement': Decimal('60.0'),
                'temperature_min': Decimal('32.0'),
                'temperature_max': Decimal('35.0'),
                'humidity_min': Decimal('60.0'),
                'humidity_max': Decimal('70.0'),
                'floor_space_per_bird': Decimal('0.3'),
                'critical_monitoring_points': json.dumps([
                    "Temperature control",
                    "Feed intake",
                    "Water access",
                    "Growth rate",
                    "Mortality monitoring"
                ]),
                'common_health_issues': json.dumps([
                    "Respiratory infections",
                    "Digestive disorders",
                    "Temperature stress",
                    "Ascites"
                ])
            },
            {
                'stage_name': 'GROWING',
                'start_week': 4,
                'end_week': 6,
                'daily_feed_per_bird': Decimal('120.0'),
                'feeding_frequency': 4,
                'water_requirement': Decimal('200.0'),
                'temperature_min': Decimal('20.0'),
                'temperature_max': Decimal('25.0'),
                'humidity_min': Decimal('50.0'),
                'humidity_max': Decimal('65.0'),
                'floor_space_per_bird': Decimal('0.7'),
                'critical_monitoring_points': json.dumps([
                    "Weight gain",
                    "Feed conversion ratio",
                    "Leg health",
                    "Uniformity",
                    "Ventilation"
                ]),
                'common_health_issues': json.dumps([
                    "Leg disorders",
                    "Heart problems",
                    "Heat stress",
                    "Sudden death syndrome"
                ])
            },
            {
                'stage_name': 'FINISHING',
                'start_week': 7,
                'end_week': 8,
                'daily_feed_per_bird': Decimal('150.0'),
                'feeding_frequency': 3,
                'water_requirement': Decimal('300.0'),
                'temperature_min': Decimal('18.0'),
                'temperature_max': Decimal('23.0'),
                'humidity_min': Decimal('50.0'),
                'humidity_max': Decimal('60.0'),
                'floor_space_per_bird': Decimal('1.0'),
                'critical_monitoring_points': json.dumps([
                    "Final weight",
                    "Feed withdrawal timing",
                    "Pre-slaughter management",
                    "Stress reduction",
                    "Processing readiness"
                ]),
                'common_health_issues': json.dumps([
                    "Heat stress",
                    "Leg weakness",
                    "Bruising",
                    "Handling stress"
                ])
            }
        ]

        for stage_data in stages_data:
            LifecycleStage.objects.get_or_create(
                breed_config=broiler_config,
                stage_name=stage_data['stage_name'],
                defaults=stage_data
            )

        # Create guidelines for broilers
        self.create_broiler_guidelines(broiler_config)

    def create_layer_guidelines(self, layer_config):
        """Create specific guidelines for layer chickens"""
        guidelines = [
            # Brooding Stage Guidelines
            {
                'guideline_type': 'FEEDING',
                'title': 'Chick Starter Feed Program',
                'description': 'Provide high-protein starter feed (20-22% protein) with appropriate particle size for chicks.',
                'applicable_from_week': 0,
                'applicable_to_week': 6,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Use crumbled or mashed feed for first 2 weeks",
                    "Ensure feed is always fresh and dry",
                    "Monitor feed intake daily",
                    "Gradually transition to pellets after 2 weeks"
                ]),
                'required_resources': json.dumps([
                    "Chick starter feed (20-22% protein)",
                    "Clean feeders",
                    "Feed storage containers"
                ]),
                'success_indicators': json.dumps([
                    "Steady weight gain",
                    "Good feed conversion",
                    "Active chick behavior"
                ])
            },
            {
                'guideline_type': 'ENVIRONMENT',
                'title': 'Brooding Temperature Management',
                'description': 'Maintain optimal temperature gradient for chick comfort and development.',
                'applicable_from_week': 0,
                'applicable_to_week': 6,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Start at 35°C for day-old chicks",
                    "Reduce temperature by 2-3°C per week",
                    "Create temperature gradient in brooder",
                    "Monitor chick behavior for comfort"
                ]),
                'required_resources': json.dumps([
                    "Heat source (infrared lamps/gas brooder)",
                    "Thermometer",
                    "Temperature controller"
                ]),
                'success_indicators': json.dumps([
                    "Chicks spread evenly under heat source",
                    "Normal activity levels",
                    "No huddling or panting"
                ])
            },
            # Growing Stage Guidelines
            {
                'guideline_type': 'FEEDING',
                'title': 'Grower Feed Transition',
                'description': 'Transition to grower feed with lower protein content for proper development.',
                'applicable_from_week': 7,
                'applicable_to_week': 16,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Switch to grower feed (16-18% protein)",
                    "Mix feeds during transition period",
                    "Monitor body weight development",
                    "Adjust feeding schedule to 3 times daily"
                ]),
                'required_resources': json.dumps([
                    "Grower feed (16-18% protein)",
                    "Feeding schedule chart",
                    "Weighing scale"
                ]),
                'success_indicators': json.dumps([
                    "Target body weight achieved",
                    "Uniform flock development",
                    "Good feather development"
                ])
            },
            # Laying Stage Guidelines
            {
                'guideline_type': 'PRODUCTION',
                'title': 'Layer Feed and Calcium Supplementation',
                'description': 'Provide layer feed with adequate calcium for egg shell formation.',
                'applicable_from_week': 17,
                'applicable_to_week': None,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Switch to layer feed (16-18% protein)",
                    "Provide calcium supplement (oyster shell)",
                    "Ensure constant access to clean water",
                    "Monitor egg production daily"
                ]),
                'required_resources': json.dumps([
                    "Layer feed",
                    "Calcium supplement",
                    "Nest boxes",
                    "Production record sheets"
                ]),
                'success_indicators': json.dumps([
                    "80%+ laying rate",
                    "Good egg shell quality",
                    "Minimal broken eggs"
                ])
            }
        ]

        for guideline_data in guidelines:
            BreedGuideline.objects.get_or_create(
                breed_config=layer_config,
                title=guideline_data['title'],
                defaults=guideline_data
            )

    def create_broiler_guidelines(self, broiler_config):
        """Create specific guidelines for broiler chickens"""
        guidelines = [
            # Brooding Stage Guidelines
            {
                'guideline_type': 'FEEDING',
                'title': 'High-Energy Broiler Starter',
                'description': 'Provide high-energy, high-protein starter feed for rapid early growth.',
                'applicable_from_week': 0,
                'applicable_to_week': 3,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Use broiler starter (22-24% protein)",
                    "Feed 6 times daily for first week",
                    "Ensure 24-hour light for first 48 hours",
                    "Monitor feed intake closely"
                ]),
                'required_resources': json.dumps([
                    "Broiler starter feed (22-24% protein)",
                    "Multiple feeders",
                    "Lighting system"
                ]),
                'success_indicators': json.dumps([
                    "Rapid weight gain",
                    "Low mortality rate",
                    "Active feeding behavior"
                ])
            },
            {
                'guideline_type': 'HEALTH',
                'title': 'Leg Health Management',
                'description': 'Prevent leg disorders through proper nutrition and management.',
                'applicable_from_week': 2,
                'applicable_to_week': 8,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Provide adequate floor space",
                    "Use proper lighting program",
                    "Monitor for lameness daily",
                    "Adjust stocking density as birds grow"
                ]),
                'required_resources': json.dumps([
                    "Timer for lighting control",
                    "Adequate floor space",
                    "Observation records"
                ]),
                'success_indicators': json.dumps([
                    "Less than 2% leg problems",
                    "Normal walking gait",
                    "Good weight distribution"
                ])
            },
            # Growing/Finishing Guidelines
            {
                'guideline_type': 'FEEDING',
                'title': 'Growth Phase Feed Management',
                'description': 'Optimize feed for maximum growth and feed conversion efficiency.',
                'applicable_from_week': 4,
                'applicable_to_week': 8,
                'priority': 'HIGH',
                'is_critical': True,
                'implementation_steps': json.dumps([
                    "Switch to grower feed (20-22% protein)",
                    "Reduce feeding frequency to 4 times daily",
                    "Monitor feed conversion ratio",
                    "Adjust feed based on growth performance"
                ]),
                'required_resources': json.dumps([
                    "Grower/finisher feed",
                    "Feed scales",
                    "Growth charts"
                ]),
                'success_indicators': json.dumps([
                    "Target weight of 2.5kg at 8 weeks",
                    "Feed conversion ratio < 2.0",
                    "Uniform flock weights"
                ])
            }
        ]

        for guideline_data in guidelines:
            BreedGuideline.objects.get_or_create(
                breed_config=broiler_config,
                title=guideline_data['title'],
                defaults=guideline_data
            )
