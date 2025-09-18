from django.contrib import admin
from .models import Farm, Device


from .models import Farm, Device, FarmMembership

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
	list_display = ("farmID", "farmName", "location", "farmSize", "owners")
	search_fields = ("farmName", "location")
	list_filter = ("farmSize",)

	def owners(self, obj):
		owners = FarmMembership.objects.filter(farm=obj, role='OWNER').select_related('farmer')
		return ", ".join([o.farmer.farmerName for o in owners]) or "-"


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
	list_display = ("deviceID", "device_id", "name", "farmID", "status")
	search_fields = ("device_id", "name")
	list_filter = ("status",)