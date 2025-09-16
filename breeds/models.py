from django.db import models

# NOTE:
# These models map to legacy PostgreSQL tables provided. Incremental improvements:
# - Added CheckConstraint for BreedCondition (condictionMin <= conditionMax)
# - Added FeedingType model to reflect feeding_type_tb (if needed later for associations)
# Future (optional): migrate integer status fields to SmallIntegerField with choices.


class BreedType(models.Model):
	breed_typeID = models.AutoField(primary_key=True)
	breedType = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name = 'Breed Type'
		verbose_name_plural = 'Breed Types'
		ordering = ['breedType']

	def __str__(self):
		return self.breedType


class Breed(models.Model):
	breedID = models.AutoField(primary_key=True)
	breedName = models.CharField(max_length=50, unique=True)
	breed_typeID = models.ForeignKey('breeds.BreedType', on_delete=models.CASCADE, related_name='breeds', db_column='breed_typeID')
	preedphoto = models.CharField(max_length=255, default='preedphoto.png', blank=True, null=True)

	class Meta:
		verbose_name = 'Breed'
		verbose_name_plural = 'Breeds'
		ordering = ['breedName']
		db_table = 'breed_tb'

	def __str__(self):
		return self.breedName


class ActivityType(models.Model):
	activityTypeID = models.AutoField(primary_key=True)
	activityType = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name = 'Activity Type'
		verbose_name_plural = 'Activity Types'
		ordering = ['activityType']
		db_table = 'activity_type_tb'

	def __str__(self):
		return self.activityType


class BreedActivity(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	breedActivityID = models.AutoField(primary_key=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_activities', db_column='breedID')
	activityTypeID = models.ForeignKey('breeds.ActivityType', on_delete=models.CASCADE, related_name='breed_activity_types', db_column='activityTypeID')
	age = models.IntegerField(default=0)
	breed_activity_status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)

	class Meta:
		verbose_name = 'Breed Activity'
		verbose_name_plural = 'Breed Activities'
		unique_together = ('breedID', 'activityTypeID', 'age')
		ordering = ['breedID', 'age']
		db_table = 'breed_activity_tb'

	def __str__(self):
		return f'{self.activityTypeID} - {self.breedID} - Age {self.age}'


class ConditionType(models.Model):
	condition_typeID = models.AutoField(primary_key=True)
	conditionName = models.CharField(max_length=50)  # Match SQL schema
	condition_unit = models.CharField(max_length=50)  # Match SQL schema

	class Meta:
		verbose_name = 'Condition Type'
		verbose_name_plural = 'Condition Types'
		ordering = ['conditionName']
		db_table = 'condition_type_tb'  # Match SQL table name

	def __str__(self):
		return f'{self.conditionName} ({self.condition_unit})'

	# Compatibility property for existing code
	@property
	def name(self):
		return self.conditionName
	
	@property
	def unit(self):
		return self.condition_unit


class BreedCondition(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	breed_conditionID = models.AutoField(primary_key=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_conditions', db_column='breedID')
	condictionMin = models.IntegerField(default=0)
	conditionMax = models.IntegerField(default=0)
	condition_status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)
	condition_typeID = models.ForeignKey('breeds.ConditionType', on_delete=models.CASCADE, related_name='breed_condition_types', db_column='condition_typeID')

	class Meta:
		verbose_name = 'Breed Condition'
		verbose_name_plural = 'Breed Conditions'
		unique_together = ('breedID', 'condition_typeID')
		ordering = ['breedID', 'condition_typeID']
		db_table = 'breed_condition_tb'
		constraints = [
			models.CheckConstraint(
				check=models.Q(condictionMin__lte=models.F('conditionMax')),
				name='breed_condition_min_le_max'
			)
		]

	def __str__(self):
		return f'{self.breedID} - {self.condition_typeID}'


class FoodType(models.Model):
	foodTypeID = models.AutoField(primary_key=True)
	foodName = models.CharField(max_length=50, unique=True)  # Match SQL schema

	class Meta:
		verbose_name = 'Food Type'
		verbose_name_plural = 'Food Types'
		ordering = ['foodName']
		db_table = 'food_type_tb'  # Match SQL table name

	def __str__(self):
		return self.foodName

	# Compatibility property for existing code
	@property
	def name(self):
		return self.foodName


class BreedFeeding(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	breedFeedingID = models.AutoField(primary_key=True)
	quantity = models.IntegerField(default=0)
	breed_feed_status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_feeding_rules', db_column='breedID')
	foodTypeID = models.ForeignKey('breeds.FoodType', on_delete=models.CASCADE, related_name='breed_feeding_types', db_column='foodTypeID')
	age = models.IntegerField(default=0)
	frequency = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Breed Feeding'
		verbose_name_plural = 'Breed Feedings'
		unique_together = ('breedID', 'foodTypeID', 'age')
		ordering = ['breedID', 'age', 'foodTypeID']
		db_table = 'breed_feeding_tb'

	def __str__(self):
		return f'{self.breedID} - {self.foodTypeID} - Age {self.age}'


class BreedGrowth(models.Model):
	breedGrowthID = models.AutoField(primary_key=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_growth', db_column='breedID')
	age = models.IntegerField(default=0)
	minWeight = models.IntegerField(default=0)

	class Meta:
		verbose_name = 'Breed Growth'
		verbose_name_plural = 'Breed Growths'
		unique_together = ('breedID', 'age')
		ordering = ['breedID', 'age']
		db_table = 'breed_growth_tb'
		indexes = [
			models.Index(fields=['breedID', 'age'], name='breed_growth_age_idx')
		]

	def __str__(self):
		return f'{self.breedID} - Age {self.age} - Min Weight: {self.minWeight}'


class FeedingType(models.Model):
	"""Represents feeding_type_tb from SQL schema."""
	feedingTypeID = models.AutoField(primary_key=True)
	feedingName = models.CharField(max_length=50, unique=True)
	quantityType = models.CharField(max_length=30)  # Fixed typo from SQL

	class Meta:
		verbose_name = 'Feeding Type'
		verbose_name_plural = 'Feeding Types'
		ordering = ['feedingName']
		db_table = 'feeding_type_tb'

	def __str__(self):
		return self.feedingName

# Import lifecycle models to make them available
from .lifecycle_models import *

# Create your models here.
