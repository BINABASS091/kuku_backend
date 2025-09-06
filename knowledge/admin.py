from django.contrib import admin
from .models import PatientHealth, Recommendation, ExceptionDisease, Anomaly, Medication


admin.site.register(PatientHealth)
admin.site.register(Recommendation)
admin.site.register(ExceptionDisease)
admin.site.register(Anomaly)
admin.site.register(Medication)

# Register your models here.
