from django.contrib import admin
from .models import SensorType, Reading


admin.site.register(SensorType)
admin.site.register(Reading)

# Register your models here.
