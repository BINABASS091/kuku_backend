from django.contrib import admin
from .models import Batch, ActivitySchedule, BatchActivity


admin.site.register(Batch)
admin.site.register(ActivitySchedule)
admin.site.register(BatchActivity)

# Register your models here.
