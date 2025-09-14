from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import User
import os


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    """Ensure an admin user exists after migrations.

    Uses environment variables if provided:
      ADMIN_USERNAME (default: admin)
      ADMIN_EMAIL (default: admin@example.com)
      ADMIN_PASSWORD (default: admin123)
    """
    # Only run once per full migrate (avoid for unrelated apps)
    if sender.name != 'accounts':
        return

    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'admin123')

    if not User.objects.filter(username=username).exists():
        user: User = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        user.role = 'ADMIN'
        user.save(update_fields=['role'])
        print(f"[init] Created default admin user '{username}'")
    else:
        # Optionally ensure role is ADMIN
        user: User = User.objects.get(username=username)
        changed = False
        if user.role != 'ADMIN':
            user.role = 'ADMIN'
            changed = True
        if not user.is_superuser or not user.is_staff:
            user.is_superuser = True
            user.is_staff = True
            changed = True
        if changed:
            user.save()
            print(f"[init] Updated existing user '{username}' to admin role")
