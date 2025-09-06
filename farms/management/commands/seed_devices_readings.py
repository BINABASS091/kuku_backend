from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from farms.models import Farm, Device
from sensors.models import SensorType, Reading


class Command(BaseCommand):
    help = "Seed a demo device on Demo Farm and a few recent sensor readings (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        farm = Farm.objects.first()
        if not farm:
            self.stdout.write(self.style.WARNING("No Farm found; skipping device/readings seed."))
            return

        device, created = Device.objects.get_or_create(
            farm=farm,
            device_id="DEV-001",
            defaults={
                "name": "Main Coop Sensor",
                "cell_no": "+255711111111",
                "picture": "device_default.png",
                "status": True,
            },
        )

        # Ensure sensor types exist
        temp = SensorType.objects.filter(name="Temperature").first()
        hum = SensorType.objects.filter(name="Humidity").first()
        if not temp or not hum:
            self.stdout.write(self.style.WARNING("Missing SensorTypes (Temperature/Humidity). Run seed_sensors first."))
            return

        # Create a few recent readings if none exist yet
        created_count = 0
        if not Reading.objects.filter(device=device).exists():
            now = timezone.now()
            samples = [
                (temp, 28.5, now - timezone.timedelta(minutes=15)),
                (hum, 62.0, now - timezone.timedelta(minutes=14)),
                (temp, 29.0, now - timezone.timedelta(minutes=5)),
                (hum, 60.5, now - timezone.timedelta(minutes=4)),
            ]
            for st, value, ts in samples:
                Reading.objects.create(device=device, sensor_type=st, value=value, timestamp=ts)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded device/readings (device_created={'yes' if created else 'no'}, readings_created={created_count})"))


