import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Carga las variables desde el archivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
# Intentamos leer la clave del .env, si no existe usamos una genérica solo para desarrollo
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Si la variable DJANGO_DEBUG es 'True', DEBUG será True. Por defecto es False para seguridad.
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

# Hosts permitidos (en Heroku debe incluir tu app: "tu-app.herokuapp.com")
ALLOWED_HOSTS = _split_env_list(os.getenv('DJANGO_ALLOWED_HOSTS'))
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else []

# Permite túneles ngrok en desarrollo local sin abrir producción.
if DEBUG:
    ALLOWED_HOSTS += ['.ngrok-free.app', '.ngrok.io']

# Seguridad CSRF
CSRF_TRUSTED_ORIGINS = _split_env_list(os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS'))
if DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app'] + CSRF_TRUSTED_ORIGINS

# --- APLICACIONES ---
INSTALLED_APPS = [
    'jazzmin', # SIEMPRE PRIMERO
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

# --- BASE DE DATOS ---
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

# --- LOCALIZACIÓN (Chile) ---
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
# Use leading and trailing slashes so STATIC_URL is absolute
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

# --- HARDENING PRODUCCIÓN (Heroku) ---
if not DEBUG:
    # Heroku termina TLS antes del dyno; esto permite que Django lo detecte
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

    # HSTS (por defecto 1 hora; sube esto cuando estés seguro)
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
    SECURE_HSTS_PRELOAD = os.getenv('DJANGO_SECURE_HSTS_PRELOAD', 'False') == 'True'

# --- CONFIGURACIÓN JAZZMIN (Milsim Theme) ---
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
    # ========== TEMA BASE ==========
    "theme": "darkly",                           # Negro profundo como base
    "dark_mode_theme": "darkly",                 # Modo oscuro = darkly
    
    # ========== IDENTIDAD VISUAL ==========
    "brand_colour": "navbar-dark",               # Navbar oscuro para el logo
    "accent": "accent-success",                  # Verde vibrante principal
    
    # ========== NAVBAR (BARRA SUPERIOR) ==========
    "navbar": "navbar-dark",                     # Negro en la barra superior
    "navbar_fixed": False,                       # No fija la navbar
    "no_navbar_border": True,                    # Elimina bordes innecesarios
    "navbar_small_text": False,                  # Texto normal
    
    # ========== SIDEBAR (MENÚ LATERAL) ==========
    "sidebar": "sidebar-dark-success",           # Sidebar oscuro con acentos verdes
    "sidebar_fixed": False,                      # No fija el sidebar
    "sidebar_disable_expand": False,             # Permite colapsar
    "sidebar_nav_small_text": False,             # Texto normal en nav
    "sidebar_nav_child_indent": True,            # Indentación visual en subitems
    "sidebar_nav_compact_style": False,          # Estilo normal, no compacto
    "sidebar_nav_legacy_style": True,            # Legacy permite más control visual
    "sidebar_nav_flat_style": False,             # No plano, con jerarquía visual
    
    # ========== LAYOUT Y ESTRUCTURA ==========
    "layout_boxed": False,                       # No boxeado, full ancho
    "footer_fixed": False,                       # Footer flotante
    "footer_small_text": False,                  # Texto normal en footer
    
    # ========== MODALES Y FORMULARIOS ==========
    "changeform_format": "single",               # Formularios en una columna
    "changeform_format_overrides": {},           # Sin overrides específicos
    
    # ========== BOTONES - CONFIGURACIÓN AGRESIVA ==========
    "button_classes": {
        "primary": "btn-success",                # Verde vibrante para botones primarios
        "secondary": "btn-secondary",            # Gris para acciones secundarias
        "info": "btn-info",                      # Azul claro para info
        "warning": "btn-warning",                # Naranja para advertencias
        "danger": "btn-danger",                  # Rojo para peligro
        "success": "btn-success"                 # Verde para éxito
    },
    
    # ========== TEXTURAS Y EFECTOS ==========
    "body_small_text": False,                    # Tamaño normal
    "brand_small_text": False,                   # Logo tamaño normal
    
    # ========== OPCIONES ADICIONALES PARA CONTRASTE ==========
    "show_ui_builder": False,                    # Desactiva el builder en vivo
    "navigation_expanded": True,                 # Menú expandido por defecto
}