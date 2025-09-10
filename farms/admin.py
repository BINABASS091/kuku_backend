from django.contrib import admin
from .models import Farm, Device


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
	list_display = ("farmID", "name", "location", "size", "farmer")
	search_fields = ("name", "location")
	list_filter = ("size",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
	list_display = ("deviceID", "device_id", "name", "farm", "status")
	search_fields = ("device_id", "name")
	list_filter = ("status",)