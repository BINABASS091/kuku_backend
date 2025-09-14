from django.contrib import admin
from .models import Farm, Device


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
	list_display = ("farmID", "farmName", "location", "farmSize", "farmerID")
	search_fields = ("farmName", "location")
	list_filter = ("farmSize",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
	list_display = ("deviceID", "device_id", "name", "farmID", "status")
	search_fields = ("device_id", "name")
	list_filter = ("status",)