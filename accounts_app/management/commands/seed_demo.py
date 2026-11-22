"""Create an idempotent, nonprivileged demo login."""

from django.core.management.base import BaseCommand, CommandError

from accounts_app.models import UserProfile


class Command(BaseCommand):
    """Provision or reset the public demo account without granting privileges."""

    help = "Create guest@example.com with the public demo password DemoGuest2026!"

    def handle(self, *args, **options):
        """Reset demo credentials only for an existing nonadministrative account."""
        user, created = UserProfile.objects.get_or_create(
            email="guest@example.com",
            defaults={"username": "guest@example.com", "fullname": "Demo Guest"},
        )
        if user.is_staff or user.is_superuser:
            raise CommandError("Refusing to reset an administrative account.")
        user.set_password("DemoGuest2026!")
        user.is_active = True
        user.save()
        self.stdout.write(
            "Demo account created." if created else "Demo password reset."
        )
