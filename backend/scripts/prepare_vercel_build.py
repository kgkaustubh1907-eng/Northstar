"""Create a per-deployment Django key when the demo has no configured secret."""

import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key


secret_file = Path("config/_deployment_secret.py")
if os.getenv("SECRET_KEY"):
    secret_file.unlink(missing_ok=True)
else:
    secret_file.write_text(
        f"SECRET_KEY = {get_random_secret_key()!r}\n",
        encoding="utf-8",
    )
