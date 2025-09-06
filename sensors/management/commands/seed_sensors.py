from django.core.management.base import BaseCommand
from django.db import transaction

from sensors.models import SensorType


class Command(BaseCommand):
    help = "Seed reference data for sensors (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        def ensure(name: str, unit: str):
            nonlocal created
            _, was_created = SensorType.objects.get_or_create(name=name, defaults={"unit": unit})
            created += 1 if was_created else 0

        ensure("Temperature", "C")
        ensure("Humidity", "%")
        ensure("CO2", "ppm")
        ensure("Ammonia", "ppm")

        self.stdout.write(self.style.SUCCESS(f"Seeded sensors (created={created})"))


