from django.db import models


class BreedType(models.Model):
	breed_typeID = models.AutoField(primary_key=True)
	breedType = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name = 'Breed Type'
		verbose_name_plural = 'Breed Types'

	def __str__(self):
		return self.breedType


class Breed(models.Model):
	breedID = models.AutoField(primary_key=True)
	breedName = models.CharField(max_length=50, unique=True)
	breed_typeID = models.ForeignKey('breeds.BreedType', on_delete=models.CASCADE, related_name='breeds', db_column='breed_typeID')
	preedphoto = models.CharField(max_length=50, default='preedphoto.png')

	class Meta:
		verbose_name = 'Breed'
		verbose_name_plural = 'Breeds'

	def __str__(self):
		return self.breedName


class ActivityType(models.Model):
	activityTypeID = models.AutoField(primary_key=True)
	activityType = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name = 'Activity Type'
		verbose_name_plural = 'Activity Types'

	def __str__(self):
		return self.activityType


class BreedActivity(models.Model):
	breedActivityID = models.AutoField(primary_key=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_activities', db_column='breedID')
	activityTypeID = models.ForeignKey('breeds.ActivityType', on_delete=models.CASCADE, related_name='breed_activity_types', db_column='activityTypeID')
	age = models.IntegerField(default=0)
	breed_activity_status = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Breed Activity'
		verbose_name_plural = 'Breed Activities'
		unique_together = ('breedID', 'activityTypeID', 'age')

	def __str__(self):
		return f'{self.activityTypeID} - {self.breedID} - Age {self.age}'


class ConditionType(models.Model):
	condition_typeID = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	unit = models.CharField(max_length=50)

	class Meta:
		verbose_name = 'Condition Type'
		verbose_name_plural = 'Condition Types'

	def __str__(self):
		return f'{self.name} ({self.unit})'


class BreedCondition(models.Model):
	breed_conditionID = models.AutoField(primary_key=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_conditions', db_column='breedID')
	condictionMin = models.IntegerField(default=0)
	conditionMax = models.IntegerField(default=0)
	condition_status = models.IntegerField(default=1)
	condition_typeID = models.ForeignKey('breeds.ConditionType', on_delete=models.CASCADE, related_name='breed_condition_types', db_column='condition_typeID')

	class Meta:
		verbose_name = 'Breed Condition'
		verbose_name_plural = 'Breed Conditions'
		unique_together = ('breedID', 'condition_typeID')

	def __str__(self):
		return f'{self.breedID} - {self.condition_typeID}'


class FoodType(models.Model):
	foodTypeID = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name = 'Food Type'
		verbose_name_plural = 'Food Types'

	def __str__(self):
		return self.name


class BreedFeeding(models.Model):
	breedFeedingID = models.AutoField(primary_key=True)
	quantity = models.IntegerField(default=0)
	breed_feed_status = models.IntegerField(default=1)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='breed_feeding_rules', db_column='breedID')
	foodTypeID = models.ForeignKey('breeds.FoodType', on_delete=models.CASCADE, related_name='breed_feeding_types', db_column='foodTypeID')
	age = models.IntegerField(default=0)
	frequency = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Breed Feeding'
		verbose_name_plural = 'Breed Feedings'
		unique_together = ('breedID', 'foodTypeID', 'age')

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

	def __str__(self):
		return f'{self.breedID} - Age {self.age} - Min Weight: {self.minWeight}'

# Create your models here.
