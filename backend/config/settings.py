import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
IS_VERCEL = os.getenv("VERCEL") == "1"
DEBUG = os.getenv("DEBUG", "False" if IS_VERCEL else "True").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY and IS_VERCEL:
    try:
        from config._deployment_secret import SECRET_KEY as deployment_secret
    except ImportError as exc:
        raise ImproperlyConfigured(
            "Vercel build did not generate the deployment secret."
        ) from exc
    SECRET_KEY = deployment_secret
SECRET_KEY = SECRET_KEY or "dev-only-change-me"
VERCEL_URL = os.getenv("VERCEL_URL", "")
ALLOWED_HOSTS = [x.strip() for x in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,.vercel.app").split(",") if x.strip()]
if VERCEL_URL and VERCEL_URL not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(VERCEL_URL)
INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "corsheaders", "rest_framework", "rest_framework.authtoken", "hospital"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
if IS_VERCEL:
    # Vercel function filesystems are ephemeral. This demo database is isolated
    # to one warm function instance and is never suitable for durable patient data.
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("HOSPITAL_SQLITE_PATH", "/tmp/hospital-demo.sqlite3"),
        "OPTIONS": {"timeout": 20},
    }}
elif os.getenv("DATABASE_URL"):
    database_url = urlparse(os.environ["DATABASE_URL"])
    if database_url.scheme not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ImproperlyConfigured("DATABASE_URL must be a PostgreSQL connection URL.")
    database_options = {key: values[-1] for key, values in parse_qs(database_url.query).items() if values}
    if not DEBUG:
        database_options.setdefault("sslmode", "require")
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(database_url.path.lstrip("/")),
        "USER": unquote(database_url.username or ""),
        "PASSWORD": unquote(database_url.password or ""),
        "HOST": database_url.hostname or "",
        "PORT": database_url.port or "5432",
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": database_options,
    }}
elif os.getenv("DB_NAME"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.getenv("DB_NAME"), "USER": os.getenv("DB_USER", "postgres"), "PASSWORD": os.getenv("DB_PASSWORD", ""), "HOST": os.getenv("DB_HOST", "localhost"), "PORT": os.getenv("DB_PORT", "5432")}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}, {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}, {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [x for x in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]
if VERCEL_URL:
    CSRF_TRUSTED_ORIGINS.append(f"https://{VERCEL_URL}")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
AUTHENTICATION_CLASSES = [
    "hospital.authentication.EphemeralVercelTokenAuthentication"
] if IS_VERCEL else ["rest_framework.authentication.TokenAuthentication"]
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": AUTHENTICATION_CLASSES, "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination", "PAGE_SIZE": 20, "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"]}
