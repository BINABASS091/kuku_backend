from django.db import models
from django.core.validators import MinValueValidator


class Farm(models.Model):
	farmID = models.AutoField(primary_key=True)
	farmName = models.CharField(max_length=200)  # Match SQL schema
	location = models.CharField(max_length=200)
	farmSize = models.CharField(max_length=50)  # Match SQL schema (string field)
	# Remove direct farmerID FK; use FarmMembership for all farmer-farm relations

	class Meta:
		verbose_name = 'Farm'
		verbose_name_plural = 'Farms'
		ordering = ['farmName']
		db_table = 'farm_tb'

	def __str__(self):
		return self.farmName

	# Compatibility properties for existing code
	@property
	def name(self):
		return self.farmName
    
	@property
	def size(self):
		return self.farmSize


# New: FarmMembership model for per-farm roles
class FarmMembership(models.Model):
	ROLE_CHOICES = (
		('OWNER', 'Owner'),
		('MANAGER', 'Manager'),
		('WORKER', 'Worker'),
	)
	farmer = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='memberships')
	farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='memberships')
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)
	joined_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('farmer', 'farm')
		db_table = 'farm_membership_tb'

	def __str__(self):
		return f"{self.farmer} - {self.farm} ({self.role})"


class Device(models.Model):
	deviceID = models.AutoField(primary_key=True)
	farmID = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='farm_devices', db_column='farmID')
	device_id = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=50)
	cell_no = models.CharField(max_length=20, default='none')
	picture = models.CharField(max_length=50, default='device_default.png')
	status = models.BooleanField(default=True)

	class Meta:
		verbose_name = 'Device'
		verbose_name_plural = 'Devices'
		ordering = ['name']
		db_table = 'device_tb'

	def __str__(self):
		return self.device_id

	# Compatibility property for existing code
	@property
	def farm(self):
		return self.farmID

# Create your models here.
