SECRET_KEY = '<CHANGE ME>'

ALLOWED_HOSTS = [
        "codery.cbigman.net",
        ]

DATABASES = {
    'default': {
        'ENGINE':'django.db.backends.postgresql_psycopg2',
        'NAME': 'codery',
        'USER': 'codery',
        'PASSWORD': '<PASSWORD>',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

DEBUG = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': None,
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
