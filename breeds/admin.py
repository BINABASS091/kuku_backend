from django.contrib import admin
from .models import (
	BreedType, Breed, ActivityType, BreedActivity,
	ConditionType, BreedCondition, FoodType, BreedFeeding, BreedGrowth
)


admin.site.register(BreedType)
admin.site.register(Breed)
admin.site.register(ActivityType)
admin.site.register(BreedActivity)
admin.site.register(ConditionType)
admin.site.register(BreedCondition)
admin.site.register(FoodType)
admin.site.register(BreedFeeding)
admin.site.register(BreedGrowth)

# Register your models here.
