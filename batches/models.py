from django.db import models
from django.utils import timezone
from decimal import Decimal


class Batch(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	# Use legacy column name as primary key for alignment
	batchID = models.AutoField(primary_key=True, db_column='batchID')
	farmID = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='batches', db_column='farmID', null=True, blank=True)
	breedID = models.ForeignKey('breeds.Breed', on_delete=models.CASCADE, related_name='batches', db_column='breedID', null=True, blank=True)
	arriveDate = models.DateField(default=timezone.now)  # Replaces sentinel date
	initAge = models.PositiveIntegerField(default=0)
	harvestAge = models.PositiveIntegerField(default=0)
	quanitity = models.PositiveIntegerField(default=0)  # legacy spelling retained
	initWeight = models.PositiveIntegerField(default=0)
	batch_status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)

	class Meta:
		verbose_name = 'Batch'
		verbose_name_plural = 'Batches'
		db_table = 'batch_tb'

	def __str__(self):
		return f'BATCH/{self.batchID}'


class ActivitySchedule(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	activityID = models.AutoField(primary_key=True, db_column='activityID')
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='schedules', db_column='batchID', null=True, blank=True)
	activityName = models.CharField(max_length=100)
	activityDescription = models.CharField(max_length=300, blank=True, default='')
	activityDay = models.CharField(max_length=10)
	activity_status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)
	activity_frequency = models.PositiveIntegerField(default=1)

	class Meta:
		verbose_name = 'Activity Schedule'
		verbose_name_plural = 'Activity Schedules'
		db_table = 'activity_schedule_tb'

	def __str__(self):
		return f'{self.activityName} - {self.batchID}'


class BatchActivity(models.Model):
	batchActivityID = models.AutoField(primary_key=True, db_column='batchActivityID')
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='activities', db_column='batchID', null=True, blank=True)
	breedActivityID = models.ForeignKey('breeds.BreedActivity', on_delete=models.CASCADE, related_name='batch_activities', db_column='breedActivityID', null=True, blank=True)
	batchActivityName = models.CharField(max_length=100)
	batchActivityDate = models.DateField(default=timezone.now)
	batchActivityDetails = models.CharField(max_length=100, blank=True, default='')
	batchAcitivtyCost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # legacy spelling retained

	class Meta:
		verbose_name = 'Batch Activity'
		verbose_name_plural = 'Batch Activities'
		db_table = 'batch_activity_tb'

	def __str__(self):
		return f'{self.batchActivityName} - {self.batchID}'


class BatchFeeding(models.Model):
	class Status(models.IntegerChoices):
		ACTIVE = 1, 'Active'
		INACTIVE = 0, 'Inactive'
		ARCHIVED = 9, 'Archived'
	batchFeedingID = models.AutoField(primary_key=True, db_column='batchFeedingID')
	batchID = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='feedings', db_column='batchID', null=True, blank=True)
	feedingDate = models.DateField(default=timezone.now)
	feedingAmount = models.PositiveIntegerField(default=0)
	status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE)

	class Meta:
		verbose_name = 'Batch Feeding'
		verbose_name_plural = 'Batch Feedings'
		db_table = 'batch_feeding_tb'

	def __str__(self):
		return f'{self.batchID} - {self.feedingDate}'

# Create your models here.
