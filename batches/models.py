from django.db import models


class Batch(models.Model):
	batchID = models.IntegerField(unique=True)  # Will become primary key after migration
	farmID = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='batches', db_column='farmID', null=True, blank=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='batches', db_column='breedID', null=True, blank=True)
	arriveDate = models.DateField(default='1900-01-01')
	initAge = models.IntegerField(default=0)
	harvestAge = models.IntegerField(default=0)
	quanitity = models.IntegerField(default=0)  # Note: keeping original spelling from PostgreSQL schema
	initWeight = models.IntegerField(default=0)
	batch_status = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Batch'
		verbose_name_plural = 'Batches'

	def __str__(self):
		return f'BATCH/{self.batchID}'


class ActivitySchedule(models.Model):
	activityID = models.IntegerField(unique=True)  # Will become primary key after migration
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='schedules', db_column='batchID', null=True, blank=True)
	activityName = models.CharField(max_length=100, default='Default Activity')
	activityDescription = models.CharField(max_length=300, default='No description')
	activityDay = models.CharField(max_length=10, default='Day')
	activity_status = models.IntegerField(default=1)
	activity_frequency = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Activity Schedule'
		verbose_name_plural = 'Activity Schedules'

	def __str__(self):
		return f'{self.activityName} - {self.batchID}'


class BatchActivity(models.Model):
	batchActivityID = models.IntegerField(unique=True, default=0)  # Will become primary key after migration
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='activities', db_column='batchID', null=True, blank=True)
	breedActivityID = models.ForeignKey('breeds.BreedActivity', on_delete=models.CASCADE, related_name='batch_activities', db_column='breedActivityID', null=True, blank=True)
	batchActivityName = models.CharField(max_length=100, default='Default Batch Activity')
	batchActivityDate = models.DateField(default='1900-01-01')
	batchActivityDetails = models.CharField(max_length=50, default='No details')
	batchAcitivtyCost = models.IntegerField(default=0)  # Note: keeping original spelling from PostgreSQL schema

	class Meta:
		verbose_name = 'Batch Activity'
		verbose_name_plural = 'Batch Activities'

	def __str__(self):
		return f'{self.batchActivityName} - {self.batchID}'


class BatchFeeding(models.Model):
	batchFeedingID = models.IntegerField(unique=True)  # Will become primary key after migration
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='feedings', db_column='batchID', null=True, blank=True)
	feedingDate = models.DateField(default='CURRENT_DATE')
	feedingAmount = models.IntegerField(default=0)
	status = models.IntegerField(default=1)

	class Meta:
		verbose_name = 'Batch Feeding'
		verbose_name_plural = 'Batch Feedings'

	def __str__(self):
		return f'{self.batchID} - {self.feedingDate}'

# Create your models here.
