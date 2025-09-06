from django.db import models


class Farm(models.Model):
	size_choices = (
		('Small', 'Small'),
		('Medium', 'Medium'),
		('Large', 'Large'),
	)
	farmer = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='farms')
	name = models.CharField(max_length=200)
	location = models.CharField(max_length=200)
	size = models.CharField(max_length=20, choices=size_choices)

	def __str__(self):
		return self.name


class Device(models.Model):
	farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='devices')
	device_id = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=50)
	cell_no = models.CharField(max_length=20, default='none')
	picture = models.CharField(max_length=50, default='device_default.png')
	status = models.BooleanField(default=True)

	def __str__(self):
		return self.device_id

# Create your models here.
