from django.contrib import admin
from .models import Batch, ActivitySchedule, BatchActivity, BatchFeeding


admin.site.register(Batch)
admin.site.register(ActivitySchedule)
admin.site.register(BatchActivity)
admin.site.register(BatchFeeding)

# Register your models here.
