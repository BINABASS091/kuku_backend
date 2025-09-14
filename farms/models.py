from django.db import models
from django.core.validators import MinValueValidator


class Farm(models.Model):
	farmID = models.AutoField(primary_key=True)
	farmer = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='farms')
	name = models.CharField(max_length=200)
	location = models.CharField(max_length=200)
	size = models.PositiveIntegerField(validators=[MinValueValidator(1)])

	class Meta:
		verbose_name = 'Farm'
		verbose_name_plural = 'Farms'
		ordering = ['name']

	def __str__(self):
		return self.name


class Device(models.Model):
	deviceID = models.AutoField(primary_key=True)
	farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='farm_devices')
	device_id = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=50)
	cell_no = models.CharField(max_length=20, default='none')
	picture = models.CharField(max_length=50, default='device_default.png')
	status = models.BooleanField(default=True)

	class Meta:
		verbose_name = 'Device'
		verbose_name_plural = 'Devices'
		ordering = ['name']

	def __str__(self):
		return self.device_id

# Create your models here.
