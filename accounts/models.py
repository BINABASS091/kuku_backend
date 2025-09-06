from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	role_choices = (
		('ADMIN', 'Administrator'),
		('FARMER', 'Farmer'),
		('ACCOUNTANT', 'Accountant'),
		('EXPERT', 'Expert'),
	)
	role = models.CharField(max_length=20, choices=role_choices, default='FARMER')
	is_active = models.BooleanField(default=True)
	profile_image = models.CharField(max_length=200, default='default.png')


class Farmer(models.Model):
	user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='farmer_profile')
	full_name = models.CharField(max_length=100)
	address = models.CharField(max_length=200)
	email = models.EmailField()
	phone = models.CharField(max_length=20)
	created_date = models.DateField(auto_now_add=True)

	def __str__(self):
		return f'{self.full_name}'

# Create your models here.
