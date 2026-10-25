import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

if os.getenv("VERCEL") == "1":
    # Each Vercel function instance gets its own temporary database. Bootstrap
    # it on cold start so the demo API can answer requests without a DB service.
    from django.core.management import call_command
    from hospital.models import Department

    call_command("migrate", interactive=False, verbosity=0)
    if not Department.objects.exists():
        call_command("seed_data", verbosity=0)
