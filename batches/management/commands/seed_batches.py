from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User, Farmer
from farms.models import Farm
from breeds.models import Breed
from batches.models import Batch


class Command(BaseCommand):
    help = "Seed a demo farm and batch if prerequisites exist (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        # Preconditions: at least one Farmer and one Breed must exist
        farmer = Farmer.objects.first()
        breed = Breed.objects.first()
        if not farmer or not breed:
            self.stdout.write(self.style.WARNING("Skip batches seed: need at least one Farmer and one Breed"))
            return

        # Ensure a farm
        farm, _ = Farm.objects.get_or_create(
            farmer=farmer, name="Demo Farm", defaults={"location": "HQ", "size": "Small"}
        )

        Batch.objects.get_or_create(
            farm=farm,
            breed=breed,
            arrive_date=timezone.now().date(),
            defaults={
                "init_age": 1,
                "harvest_age": 42,
                "quantity": 100,
                "init_weight": 40,
                "status": 1,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo batch (idempotent)"))


