
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create default IT MUCE role groups"

    def handle(self, *args, **options):
        roles = ["Member", "Editor", "Admin"]

        for role in roles:
            group, created = Group.objects.get_or_create(name=role)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created role: {role}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Role already exists: {role}")
                )

        self.stdout.write(
            self.style.SUCCESS("IT MUCE roles are ready.")
        )
