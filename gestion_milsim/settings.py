from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-cambia-esto-por-seguridad'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Seguridad para Ngrok
CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app']

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# --- CONFIGURACIÓN VISUAL (SOLUCIÓN A PUNTOS I, VI, VII) ---
JAZZMIN_SETTINGS = {
    "site_title": "MANDO CENTRAL",
    "site_header": "75th RANGER RGT",
    "site_brand": "OPS CENTER",
    "welcome_sign": "Sistema de Gestión Clasificado",
    "copyright": "LatamSquad Engineering",
    "search_model": "orbat.Miembro",
    "user_avatar": None,
    
    # --- ESTO SOLUCIONA EL PROBLEMA DE LAS PESTAÑAS VACÍAS ---
    # "single" pone todo en una sola página vertical (scrolleas y ves todo).
    "changeform_format": "single", 
    
    # Menú Lateral
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
    "custom_js": None,

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
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": False,
    "theme": "darkly", # TEMA OSCURO
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}