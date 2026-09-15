import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.adminconfig.models import PipelineSettings, PromptTemplate, StorageSettings


class Command(BaseCommand):
    help = "Seed default PipelineSettings, StorageSettings, prompt templates, and (optionally) an admin user."

    def handle(self, *args, **options):
        if not PipelineSettings.objects.exists():
            PipelineSettings.objects.create()
            self.stdout.write(self.style.SUCCESS("Created default PipelineSettings."))

        if not StorageSettings.objects.exists():
            StorageSettings.get_active()
            self.stdout.write(self.style.SUCCESS("Created default StorageSettings."))

        if not PromptTemplate.objects.filter(is_default=True, category="").exists():
            PromptTemplate.objects.create(name="Default Studio Recreation", category="", is_default=True)
            self.stdout.write(self.style.SUCCESS("Created default PromptTemplate."))

        admin_email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        admin_password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if admin_email and admin_password and not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(admin_email, admin_password)
            self.stdout.write(self.style.SUCCESS(f"Created admin user {admin_email}."))

        self.stdout.write(self.style.SUCCESS("Seed complete."))
