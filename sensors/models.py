from django.db import models


class SensorType(models.Model):
	sensorTypeID = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50, unique=True)
	unit = models.CharField(max_length=20)

	class Meta:
		verbose_name = 'Sensor Type'
		verbose_name_plural = 'Sensor Types'
		ordering = ['name']

	def __str__(self):
		return f'{self.name} ({self.unit})'


class Reading(models.Model):
	readingID = models.AutoField(primary_key=True)
	deviceID = models.ForeignKey('farms.Device', on_delete=models.CASCADE, related_name='readings', db_column='deviceID', null=True, blank=True)
	sensor_typeID = models.ForeignKey('sensors.SensorType', on_delete=models.CASCADE, related_name='readings', db_column='sensor_typeID', null=True, blank=True)
	value = models.FloatField(default=0.0)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Reading'
		verbose_name_plural = 'Readings'
		indexes = [
			models.Index(fields=['deviceID', 'timestamp']),
		]

	def __str__(self):
		return f'{self.deviceID} - {self.sensor_typeID} - {self.timestamp}'

# Create your models here.
