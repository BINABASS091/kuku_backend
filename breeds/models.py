from django.db import models


class BreedType(models.Model):
	name = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.name


class Breed(models.Model):
	name = models.CharField(max_length=50, unique=True)
	type = models.ForeignKey('breeds.BreedType', on_delete=models.PROTECT, related_name='breeds')
	photo = models.CharField(max_length=100, default='preedphoto.png')

	def __str__(self):
		return self.name


class ActivityType(models.Model):
	name = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.name


class BreedActivity(models.Model):
	breed = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='activities')
	activity_type = models.ForeignKey('breeds.ActivityType', on_delete=models.PROTECT, related_name='breed_activities')
	age = models.IntegerField()
	status = models.BooleanField(default=True)

	class Meta:
		unique_together = ('breed', 'activity_type', 'age')


class ConditionType(models.Model):
	name = models.CharField(max_length=50, unique=True)
	unit = models.CharField(max_length=50)

	def __str__(self):
		return f'{self.name} ({self.unit})'


class BreedCondition(models.Model):
	breed = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='conditions')
	condition_type = models.ForeignKey('breeds.ConditionType', on_delete=models.PROTECT, related_name='breed_conditions')
	min_value = models.IntegerField()
	max_value = models.IntegerField()
	status = models.BooleanField(default=True)

	class Meta:
		unique_together = ('breed', 'condition_type')


class FoodType(models.Model):
	name = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.name


class BreedFeeding(models.Model):
	breed = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='feeding_rules')
	food_type = models.ForeignKey('breeds.FoodType', on_delete=models.PROTECT, related_name='breed_feeding')
	age = models.IntegerField()
	quantity = models.IntegerField(default=0)
	frequency = models.IntegerField()
	status = models.BooleanField(default=True)

	class Meta:
		unique_together = ('breed', 'food_type', 'age')


class BreedGrowth(models.Model):
	breed = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='growth')
	age = models.IntegerField()
	min_weight = models.IntegerField()

	class Meta:
		unique_together = ('breed', 'age')

# Create your models here.
