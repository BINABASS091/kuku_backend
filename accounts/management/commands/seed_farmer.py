from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User, Farmer


class Command(BaseCommand):
    help = "Seed a demo Farmer linked to the existing admin user if present, otherwise create a new demo user (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        # Prefer existing user named 'admin' if it exists; else create demo user
        user = User.objects.filter(username="admin").first()
        if user is None:
            if not User.objects.filter(username="demo_farmer").exists():
                user = User.objects.create_user(
                    username="demo_farmer",
                    email="demo_farmer@example.com",
                    password="demo12345",
                    role="FARMER",
                )
            else:
                user = User.objects.get(username="demo_farmer")

        farmer, created = Farmer.objects.get_or_create(
            user=user,
            defaults={
                "full_name": "Demo Farmer",
                "address": "Demo Address",
                "email": user.email or "demo_farmer@example.com",
                "phone": "+255700000000",
            },
        )

        if not created:
            # Ensure sensible defaults exist
            changed = False
            if not farmer.full_name:
                farmer.full_name = "Demo Farmer"; changed = True
            if not farmer.address:
                farmer.address = "Demo Address"; changed = True
            if not farmer.email:
                farmer.email = user.email or "demo_farmer@example.com"; changed = True
            if not farmer.phone:
                farmer.phone = "+255700000000"; changed = True
            if changed:
                farmer.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded demo farmer: user={user.username}, farmer_id={farmer.id}"
        ))


