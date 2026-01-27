"""
Load categories + sample data for local/Docker development.
Single command to bootstrap a full dev dataset.

Usage:
    python manage.py load_dev_data
    python manage.py load_dev_data --reset   # Wipe and reload categories + sample data
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load categories and sample data for development (runs load_categories then load_sample_data)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing categories and sample data, then reload",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        self.stdout.write(self.style.SUCCESS("Loading dev data (categories + sample)..."))

        call_command("load_categories", reset=reset)
        call_command("load_sample_data", reset=reset)

        self.stdout.write(self.style.SUCCESS("Dev data ready. Sample users password: sample123"))
