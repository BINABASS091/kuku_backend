from django.core.management.base import BaseCommand
from django.db import transaction

from breeds.models import (
    BreedType, Breed, ActivityType, ConditionType,
    FoodType, BreedFeeding, BreedGrowth
)


class Command(BaseCommand):
    help = "Seed reference data for breeds (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        created_counts = {}

        def get_or_create(model, defaults=None, **kwargs):
            obj, created = model.objects.get_or_create(defaults=defaults or {}, **kwargs)
            created_counts[model.__name__] = created_counts.get(model.__name__, 0) + (1 if created else 0)
            return obj

        # Reference types
        broiler = get_or_create(BreedType, name="Broiler")
        kroiler = get_or_create(BreedType, name="Kroiler")

        act_feed = get_or_create(ActivityType, name="Feeding")
        act_vacc = get_or_create(ActivityType, name="Vaccination")

        cond_temp = get_or_create(ConditionType, name="Temperature", defaults={"unit": "C"})
        cond_hum = get_or_create(ConditionType, name="Humidity", defaults={"unit": "%"})

        food_starter = get_or_create(FoodType, name="Starter")
        food_grower = get_or_create(FoodType, name="Grower")

        # Demo breed
        cobb500 = get_or_create(Breed, name="Cobb 500", defaults={"type": kroiler, "photo": "preedphoto.png"})
        if cobb500.type_id != kroiler.id:
            cobb500.type = kroiler
            cobb500.save(update_fields=["type"])

        # Feeding rules
        get_or_create(BreedFeeding, breed=cobb500, food_type=food_starter, age=1, defaults={
            "quantity": 25, "frequency": 3, "status": True,
        })
        get_or_create(BreedFeeding, breed=cobb500, food_type=food_starter, age=7, defaults={
            "quantity": 45, "frequency": 3, "status": True,
        })

        # Growth targets
        get_or_create(BreedGrowth, breed=cobb500, age=7, defaults={"min_weight": 180})
        get_or_create(BreedGrowth, breed=cobb500, age=14, defaults={"min_weight": 420})
        get_or_create(BreedGrowth, breed=cobb500, age=21, defaults={"min_weight": 750})

        # Conditions (optional min/max exemplars could be in another seed)
        # Keeping minimal here as conditions are posted separately

        self.stdout.write(self.style.SUCCESS(
            f"Seeded breeds data (created counts): {created_counts}"
        ))


