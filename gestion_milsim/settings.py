import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Carga variables del archivo .env
load_dotenv()

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# DEBUG se controla por variable de entorno
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
IS_TESTING = 'test' in sys.argv

if not SECRET_KEY and DEBUG:
    SECRET_KEY = 'django-insecure-desarrollo-local'
if not SECRET_KEY and not DEBUG:
    raise ValueError('Falta DJANGO_SECRET_KEY en producción')

def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]

# Hosts permitidos
ALLOWED_HOSTS = _split_env_list(os.getenv('DJANGO_ALLOWED_HOSTS'))
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else []

# Soporte ngrok solo en desarrollo
if DEBUG:
    ALLOWED_HOSTS += ['.ngrok-free.app', '.ngrok.io']

# Orígenes confiables para CSRF
CSRF_TRUSTED_ORIGINS = _split_env_list(os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS'))
if DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app'] + CSRF_TRUSTED_ORIGINS

# Aplicaciones
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'orbat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'orbat.middleware.BlockAdminCredentialChangesMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_milsim.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_milsim.wsgi.application'

# Base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=int(os.getenv('DJANGO_CONN_MAX_AGE', '600')),
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Localización
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if (DEBUG or IS_TESTING)
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Producción (Heroku)
if not DEBUG:
    # Django debe confiar en el encabezado de proxy HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

    # HSTS
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
    SECURE_HSTS_PRELOAD = os.getenv('DJANGO_SECURE_HSTS_PRELOAD', 'False') == 'True'

# Configuración Jazzmin
JAZZMIN_SETTINGS = {
    "site_title": "MANDO CENTRAL",
    "site_header": "75th RANGER RGT",
    "site_brand": "OPS CENTER",
    "welcome_sign": "Sistema de Gestión Clasificado",
    "copyright": "LatamSquad Engineering",
    "search_model": "orbat.Miembro",
    "user_avatar": None,
    
    "changeform_format": "single", 
    
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_models": ["orbat.Fase"],
    
    "order_with_respect_to": [
        "orbat.Regimiento", 
        "orbat.Compania", 
        "orbat.Peloton",
        "orbat.Escuadra", 
        "orbat.Miembro", 
        "orbat.Curso"
    ],

    "icons": {
        "auth": "fas fa-shield-alt",
        "auth.user": "fas fa-user-lock",
        "orbat.Regimiento": "fas fa-landmark",
        "orbat.Compania": "fas fa-sitemap",
        "orbat.Peloton": "fas fa-th-large",
        "orbat.Escuadra": "fas fa-users",
        "orbat.Miembro": "fas fa-id-card",
        "orbat.Curso": "fas fa-graduation-cap",
    },

    "custom_css": "custom_admin.css",
    "dashboard_widgets": [
        {
            "view": "admin:orbat_miembro_changelist",
            "title": "Fuerza Operativa",
            "icon": "fas fa-users",
            "color": "primary",
        }
    ]
}

JAZZMIN_UI_TWEAKS = {
    # Tema
    "theme": "darkly",
    "dark_mode_theme": "darkly",

    # Colores
    "brand_colour": "navbar-dark",
    "accent": "accent-success",

    # Barra superior
    "navbar": "navbar-dark",
    "navbar_fixed": False,
    "no_navbar_border": True,
    "navbar_small_text": False,

    # Sidebar
    "sidebar": "sidebar-dark-success",
    "sidebar_fixed": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_small_text": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": False,

    # Layout
    "layout_boxed": False,
    "footer_fixed": False,
    "footer_small_text": False,

    # Formularios
    "changeform_format": "single",
    "changeform_format_overrides": {},

    # Botones
    "button_classes": {
        "primary": "btn-success",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },

    # Ajustes generales
    "body_small_text": False,
    "brand_small_text": False,
    "show_ui_builder": False,
    "navigation_expanded": True,
}