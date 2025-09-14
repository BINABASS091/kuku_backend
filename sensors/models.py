from django.db import models


class SensorType(models.Model):
	sensorTypeID = models.AutoField(primary_key=True)
	sensorTypeName = models.CharField(max_length=50, unique=True)  # Match SQL schema
	measurementUnit = models.CharField(max_length=20)  # Match SQL schema

	class Meta:
		verbose_name = 'Sensor Type'
		verbose_name_plural = 'Sensor Types'
		ordering = ['sensorTypeName']
		db_table = 'sensor_type_tb'  # Match SQL table name

	def __str__(self):
		return f'{self.sensorTypeName} ({self.measurementUnit})'

	# Compatibility properties for existing code
	@property
	def name(self):
		return self.sensorTypeName
	
	@property
	def unit(self):
		return self.measurementUnit


class Reading(models.Model):
	readingID = models.AutoField(primary_key=True)
	deviceID = models.ForeignKey('farms.Device', on_delete=models.CASCADE, related_name='readings', db_column='deviceID', null=True, blank=True)
	sensor_typeID = models.ForeignKey('sensors.SensorType', on_delete=models.CASCADE, related_name='readings', db_column='sensor_typeID', null=True, blank=True)
	value = models.FloatField(default=0.0)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Reading'
		verbose_name_plural = 'Readings'
		db_table = 'reading_tb'
		indexes = [
			models.Index(fields=['deviceID', 'timestamp']),
		]

	def __str__(self):
		return f'{self.deviceID} - {self.sensor_typeID} - {self.timestamp}'

# Create your models here.
