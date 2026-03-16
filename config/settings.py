import os
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = config('SECRET_KEY', default='eco-refill-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'cloudinary_storage',  # 1. SIEMPRE debe ir antes de staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # 2. staticfiles va después de storage
    
    # Librerías de terceros
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'cloudinary', # 3. La librería base suele ir al final de las de terceros
    
    # Tus aplicaciones locales
    'apps.users',
    'apps.tasks',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Agregado
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Agregado
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Agregado
    'django.contrib.messages.middleware.MessageMiddleware', # Agregado
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Agregado
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', # Agregado
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', # Agregado
                'django.contrib.messages.context_processors.messages', # Agregado
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {}

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Eco-Refill API',
    'DESCRIPTION': 'Sistema de recargas de productos de aseo - Eco-Refill',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='')
FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', config('FIREBASE_WEB_API_KEY', default=''))

CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', config('CLOUDINARY_CLOUD_NAME', default=''))
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', config('CLOUDINARY_API_KEY', default=''))
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', config('CLOUDINARY_API_SECRET', default=''))
