from django.db import models


class SensorType(models.Model):
	name = models.CharField(max_length=50, unique=True)
	unit = models.CharField(max_length=20)

	def __str__(self):
		return f'{self.name} ({self.unit})'


class Reading(models.Model):
	device = models.ForeignKey('farms.Device', on_delete=models.CASCADE, related_name='readings')
	sensor_type = models.ForeignKey('sensors.SensorType', on_delete=models.PROTECT, related_name='readings')
	value = models.FloatField()
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['device', 'timestamp']),
		]

# Create your models here.
