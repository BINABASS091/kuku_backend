from django.db import models


class Batch(models.Model):
	status_choices = (
		(0, 'Pending'),
		(1, 'Ongoing'),
		(2, 'Completed'),
	)
	farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='batches')
	breed = models.ForeignKey('breeds.Breed', on_delete=models.PROTECT, related_name='batches')
	arrive_date = models.DateField()
	init_age = models.IntegerField()
	harvest_age = models.IntegerField(default=0)
	quantity = models.IntegerField()
	init_weight = models.IntegerField()
	status = models.IntegerField(choices=status_choices, default=1)

	def __str__(self):
		return f'BATCH/{self.id}'


class ActivitySchedule(models.Model):
	period_choices = (
		('Day', 'Day'),
		('Week', 'Week'),
		('Month', 'Month'),
	)
	batch = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='schedules')
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=300)
	period = models.CharField(max_length=10, choices=period_choices, default='Day')
	frequency = models.IntegerField()
	status = models.BooleanField(default=True)

	class Meta:
		unique_together = ('batch', 'name')


class BatchActivity(models.Model):
	batch = models.ForeignKey('batches.Batch', on_delete=models.CASCADE, related_name='activities')
	breed_activity = models.ForeignKey('breeds.BreedActivity', on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_activities')
	name = models.CharField(max_length=100)
	date = models.DateField()
	details = models.CharField(max_length=200)
	cost = models.IntegerField(default=0)

# Create your models here.
