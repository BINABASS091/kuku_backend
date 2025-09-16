"""
Breed Lifecycle Guidance System Models

This module extends the existing breed models to provide comprehensive
lifecycle guidance for farmers based on breed type and age.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class BreedConfiguration(models.Model):
    """
    Master configuration for each breed type defining lifecycle parameters
    """
    BREED_PURPOSE_CHOICES = [
        ('EGGS', 'Egg Production'),
        ('MEAT', 'Meat Production'),
        ('DUAL', 'Dual Purpose'),
    ]
    
    LIFECYCLE_STAGE_CHOICES = [
        ('BROODING', 'Brooding (0-6 weeks)'),
        ('GROWING', 'Growing (7-16 weeks)'),
        ('LAYING', 'Laying (17+ weeks)'),
        ('FINISHING', 'Finishing (6-8 weeks for meat)'),
    ]
    
    configuration_id = models.AutoField(primary_key=True)
    breed = models.OneToOneField('breeds.Breed', on_delete=models.CASCADE, related_name='lifecycle_config')
    purpose = models.CharField(max_length=10, choices=BREED_PURPOSE_CHOICES, default='EGGS')
    
    # Lifecycle timing (in weeks)
    brooding_end_week = models.IntegerField(default=6, validators=[MinValueValidator(1), MaxValueValidator(12)])
    growing_end_week = models.IntegerField(default=16, validators=[MinValueValidator(7), MaxValueValidator(24)])
    laying_start_week = models.IntegerField(default=17, validators=[MinValueValidator(16), MaxValueValidator(30)])
    slaughter_week = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(6), MaxValueValidator(20)])
    
    # Performance targets
    expected_laying_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('80.00'), help_text="Expected laying rate percentage")
    target_weight_at_slaughter = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Target weight in grams")
    
    # Basic parameters
    optimal_temperature_min = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('18.0'))
    optimal_temperature_max = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('25.0'))
    optimal_humidity_min = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('50.0'))
    optimal_humidity_max = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('70.0'))
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'breed_configuration_tb'
        verbose_name = 'Breed Configuration'
        verbose_name_plural = 'Breed Configurations'
    
    def __str__(self):
        return f"{self.breed.breedName} - {self.get_purpose_display()}"
    
    def get_current_stage(self, age_in_weeks):
        """Determine current lifecycle stage based on age"""
        if age_in_weeks <= self.brooding_end_week:
            return 'BROODING'
        elif age_in_weeks <= self.growing_end_week:
            return 'GROWING'
        elif self.purpose == 'MEAT' and self.slaughter_week and age_in_weeks >= self.slaughter_week:
            return 'FINISHING'
        else:
            return 'LAYING'


class LifecycleStage(models.Model):
    """
    Detailed configuration for each lifecycle stage
    """
    stage_id = models.AutoField(primary_key=True)
    breed_config = models.ForeignKey(BreedConfiguration, on_delete=models.CASCADE, related_name='stages')
    stage_name = models.CharField(max_length=20, choices=BreedConfiguration.LIFECYCLE_STAGE_CHOICES)
    
    # Age range for this stage
    start_week = models.IntegerField(validators=[MinValueValidator(0)])
    end_week = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Stage-specific parameters
    daily_feed_per_bird = models.DecimalField(max_digits=6, decimal_places=2, help_text="Grams per bird per day")
    feeding_frequency = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(6)])
    water_requirement = models.DecimalField(max_digits=6, decimal_places=2, help_text="ML per bird per day")
    
    # Environmental requirements
    temperature_min = models.DecimalField(max_digits=4, decimal_places=1)
    temperature_max = models.DecimalField(max_digits=4, decimal_places=1)
    humidity_min = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('50.0'))
    humidity_max = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('70.0'))
    
    # Space requirements
    floor_space_per_bird = models.DecimalField(max_digits=6, decimal_places=2, help_text="Square feet per bird")
    
    # Health and monitoring
    critical_monitoring_points = models.TextField(help_text="JSON array of monitoring points")
    common_health_issues = models.TextField(help_text="JSON array of common health issues")
    
    class Meta:
        db_table = 'lifecycle_stage_tb'
        verbose_name = 'Lifecycle Stage'
        verbose_name_plural = 'Lifecycle Stages'
        unique_together = ['breed_config', 'stage_name']
        ordering = ['breed_config', 'start_week']
    
    def __str__(self):
        return f"{self.breed_config.breed.breedName} - {self.get_stage_name_display()}"


class BreedGuideline(models.Model):
    """
    Specific guidelines and best practices for each breed and stage
    """
    GUIDELINE_TYPES = [
        ('FEEDING', 'Feeding Guidelines'),
        ('HEALTH', 'Health Management'),
        ('ENVIRONMENT', 'Environmental Control'),
        ('BREEDING', 'Breeding Management'),
        ('PRODUCTION', 'Production Optimization'),
        ('GENERAL', 'General Care'),
    ]
    
    guideline_id = models.AutoField(primary_key=True)
    breed_config = models.ForeignKey(BreedConfiguration, on_delete=models.CASCADE, related_name='guidelines')
    stage = models.ForeignKey(LifecycleStage, on_delete=models.CASCADE, related_name='guidelines', null=True, blank=True)
    
    guideline_type = models.CharField(max_length=20, choices=GUIDELINE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Timing
    applicable_from_week = models.IntegerField(default=0)
    applicable_to_week = models.IntegerField(null=True, blank=True)
    
    # Priority and categorization
    priority = models.CharField(max_length=10, choices=[
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ], default='MEDIUM')
    
    is_critical = models.BooleanField(default=False, help_text="Critical for bird health/production")
    is_automated = models.BooleanField(default=False, help_text="Can be automated by system")
    
    # Implementation details
    implementation_steps = models.TextField(help_text="JSON array of implementation steps")
    required_resources = models.TextField(help_text="JSON array of required resources")
    success_indicators = models.TextField(help_text="JSON array of success indicators")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'breed_guideline_tb'
        verbose_name = 'Breed Guideline'
        verbose_name_plural = 'Breed Guidelines'
        ordering = ['breed_config', 'applicable_from_week', 'priority']
    
    def __str__(self):
        return f"{self.breed_config.breed.breedName} - {self.title}"


class FarmBreedPlan(models.Model):
    """
    Farmer's specific breed plan and progress tracking
    """
    plan_id = models.AutoField(primary_key=True)
    farmer = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='breed_plans')
    batch = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='breed_plan')
    breed_config = models.ForeignKey(BreedConfiguration, on_delete=models.CASCADE, related_name='farm_plans')
    
    # Plan details
    start_date = models.DateField()
    planned_end_date = models.DateField()
    initial_bird_count = models.IntegerField()
    current_bird_count = models.IntegerField()
    
    # Current status
    current_age_weeks = models.DecimalField(max_digits=4, decimal_places=1)
    current_stage = models.CharField(max_length=20, choices=BreedConfiguration.LIFECYCLE_STAGE_CHOICES)
    
    # Performance tracking
    actual_feed_consumption = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    mortality_count = models.IntegerField(default=0)
    health_issues_count = models.IntegerField(default=0)
    
    # Production tracking (for layers)
    total_eggs_collected = models.IntegerField(default=0)
    current_laying_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
    ], default='ACTIVE')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_breed_plan_tb'
        verbose_name = 'Farm Breed Plan'
        verbose_name_plural = 'Farm Breed Plans'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.farmer.farmerName} - {self.breed_config.breed.breedName} - {self.start_date}"
    
    def get_current_guidelines(self):
        """Get applicable guidelines for current stage and age"""
        return BreedGuideline.objects.filter(
            breed_config=self.breed_config,
            applicable_from_week__lte=self.current_age_weeks,
            is_active=True
        ).filter(
            models.Q(applicable_to_week__isnull=True) | 
            models.Q(applicable_to_week__gte=self.current_age_weeks)
        )


class GuidelineCompletion(models.Model):
    """
    Track farmer's completion of guidelines
    """
    completion_id = models.AutoField(primary_key=True)
    farm_plan = models.ForeignKey(FarmBreedPlan, on_delete=models.CASCADE, related_name='completions')
    guideline = models.ForeignKey(BreedGuideline, on_delete=models.CASCADE, related_name='completions')
    
    # Completion details
    completed_at = models.DateTimeField()
    completion_notes = models.TextField(blank=True)
    success_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 rating of implementation success"
    )
    
    # Results tracking
    measured_results = models.TextField(blank=True, help_text="JSON of measured outcomes")
    farmer_feedback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'guideline_completion_tb'
        verbose_name = 'Guideline Completion'
        verbose_name_plural = 'Guideline Completions'
        unique_together = ['farm_plan', 'guideline']
    
    def __str__(self):
        return f"{self.farm_plan.farmer.farmerName} - {self.guideline.title}"
