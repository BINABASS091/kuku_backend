from django.core.management.base import BaseCommand
from farms.models import Farm, FarmMembership
from accounts.models import Farmer

class Command(BaseCommand):
    help = "Backfill FarmMemberships for all existing farms, assigning previous farmer as OWNER."

    # Paste your mapping here: {farmID: farmerID, ...}
    FARM_OWNER_MAP = {
        # Example: 1: 2, 2: 3
        # Fill this with your real data from backup
    }

    def handle(self, *args, **options):
        count = 0
        for farm_id, farmer_id in self.FARM_OWNER_MAP.items():
            try:
                farm = Farm.objects.get(farmID=farm_id)
                farmer = Farmer.objects.get(pk=farmer_id)
                obj, created = FarmMembership.objects.get_or_create(farm=farm, farmer=farmer, defaults={'role': 'OWNER'})
                if created:
                    count += 1
                    self.stdout.write(f"[OK] Created OWNER membership: farm {farm.farmName} (ID {farm.farmID}) -> farmer {farmer.farmerName} (ID {farmer.pk})")
                else:
                    self.stdout.write(f"[SKIP] Membership already exists: farm {farm.farmName} (ID {farm.farmID}) -> farmer {farmer.farmerName} (ID {farmer.pk})")
            except Exception as e:
                self.stdout.write(f"[ERROR] farmID {farm_id}, farmerID {farmer_id}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Backfill complete. {count} memberships created."))
