"""Create fictional demo data only when the shared database is empty."""

import os

import django
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from hospital.models import Department  # noqa: E402


if Department.objects.exists():
    print("Existing hospital data found; skipping demo seed.")
else:
    call_command("seed_data", verbosity=1)
