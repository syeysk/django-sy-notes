from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['*']),
    SITE_URL=(str, 'http://127.0.0.1'),
)
environ.Env.read_env(env_file=BASE_DIR / '.env')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')
DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
METRIC_SYSTEM_CODE = env.str('METRIC_SYSTEM_CODE', default='', multiline=True)
HIDE_METRIC_FOR = env.list('HIDE_METRIC_FOR', default=list())
ROOT_URLCONF = 'server.urls'
WSGI_APPLICATION = 'server.wsgi.application'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent / 'static'
SITE_URL = env('SITE_URL')
INTERNAL_IPS = ['127.0.0.1']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'media'

SALT = env('SALT')
API_SALT = env('API_SALT')
API_SECRET_KEY = env('API_SECRET_KEY')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'markdownify.apps.MarkdownifyConfig',
    'django_sy_framework.base',
    'django_sy_framework.custom_auth',
    'django_sy_framework.linker',
    'server',
    'note',
    'pages',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_sy_framework.custom_auth.context_processors.extern_auth_services',
                'django_sy_framework.base.context_processors.settings_variables',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / '.sqlite3.db',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / '.debug.log',
            'formatter': 'main',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API микросервиса заметок',
    'DESCRIPTION': 'Сервер предоставляет доступ к манипулированию заметками',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'SCHEMA_PATH_PREFIX_INSERT': 'api',
    #'SCHEMA_PATH_PREFIX': '/api/v[0-9]',
    'SERVE_URLCONF': 'server.urls_api',
    'SERVERS': [{'url': f'{SITE_URL}'}],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# External auth

EXTERN_AUTH = {
    'google': {
        'client_id': env('EXTERN_AUTH_GOOGLE_CLIENT_ID'),
        'client_secret': env('EXTERN_AUTH_GOOGLE_CLIENT_SECRET'),
    }
}

AUTH_USER_MODEL = 'custom_auth.CustomAuthUser'
AUTHENTICATION_BACKENDS = ['django_sy_framework.custom_auth.backend.CustomAuthBackend']
MICROSERVICES_TOKENS = {
    'from_platform': env('MICROSERVICE_TOKEN_FROM_PLATFORM'),
}
MICROSERVICES_URLS = {
    'auth': env('MICROSERVICE_URL_AUTH'),
}

# Knowledge app

DEFAULT_SOURCE_SERVICE_NAME = env('DEFAULT_SOURCE_SERVICE_NAME')
DEFAULT_SOURCE_CREDENTIALS = env('DEFAULT_SOURCE_CREDENTIALS')
DEFAULT_SOURCE_CODE = env('DEFAULT_SOURCE_CODE')

MARKDOWNIFY = {
    'default': {
        'BLEACH': False,
        'MARKDOWN_EXTENSIONS': [
            'utils.md_extensions.obsidian_links:ObsidianLinksExtension',
            'utils.md_extensions.wiki_links:WikiLinksExtension',
            'utils.md_extensions.internal_images:InternalImagesExtension',
            'utils.md_extensions.tags_like_links:TagsLikeLinksExtension',
            'md_mermaid',
        ],
    }
}
