from django.core.management.base import BaseCommand
from django.db import transaction

from subscriptions.models import SubscriptionType, Resource


class Command(BaseCommand):
    help = "Seed subscription plans and resources (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        created_counts = {"SubscriptionType": 0, "Resource": 0}

        def get_or_create(model, defaults=None, **kwargs):
            obj, created = model.objects.get_or_create(defaults=defaults or {}, **kwargs)
            created_counts[model.__name__] += 1 if created else 0
            return obj

        # Plans
        get_or_create(SubscriptionType, name="Starter", defaults={
            "farm_size": "Small", "cost": 0, "description": "Free tier"
        })
        get_or_create(SubscriptionType, name="Pro", defaults={
            "farm_size": "Medium", "cost": 29900, "description": "Pro features"
        })
        get_or_create(SubscriptionType, name="Enterprise", defaults={
            "farm_size": "Large", "cost": 99900, "description": "All features"
        })

        # Resources
        get_or_create(Resource, name="Smart Device", defaults={
            "resource_type": 1, "unit_cost": 150000, "status": True
        })
        get_or_create(Resource, name="Advanced Analytics", defaults={
            "resource_type": 3, "unit_cost": 59000, "status": True
        })
        get_or_create(Resource, name="Prediction Engine", defaults={
            "resource_type": 4, "unit_cost": 79000, "status": True
        })

        self.stdout.write(self.style.SUCCESS(
            f"Seeded subscriptions (created counts): {created_counts}"
        ))


