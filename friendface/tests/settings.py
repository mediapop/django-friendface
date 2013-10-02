import os

SITE_ID = 1

APP_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

AUTHENTICATION_BACKENDS = (
    'friendface.auth.backends.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend'
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    'friendface.tests.accounts',
    'friendface',
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'friendface.middleware.FacebookApplicationMiddleware',
    'friendface.middleware.FacebookDecodingMiddleware',
    'friendface.middleware.DisableCsrfProtectionOnDecodedSignedRequest',
    'friendface.middleware.FacebookSignedRequestAuthenticationMiddleware',
)

SECRET_KEY = 'foobar'

TEST_RUNNER = 'discover_runner.DiscoverRunner'

ROOT_URLCONF = 'friendface.tests.urls'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'
