import sys
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    ROOT_URLCONF='test.testurlconf',
    AUTH_PROFILE_MODULE='accounts.UserProfile',
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.staticfiles',
        'django_nose',
        'test.accounts',
        'friendface',
    ),
    NOSE_ARGS=['--verbosity=0', '--nocapture'],
    STATIC_URL='/static/',
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'friendface.middleware.FacebookApplicationMiddleware',
        'friendface.middleware.FacebookDecodingMiddleware',
        'friendface.middleware.DisableCsrfProtectionOnDecodedSignedRequest',
        'friendface.middleware.FacebookSignedRequestAuthenticationMiddleware',
    ),
    AUTHENTICATION_BACKENDS=(
        'friendface.auth.backends.FacebookBackend',
        'django.contrib.auth.backends.ModelBackend'
    ),
)

# from django.test.simple import DjangoTestSuiteRunner
# test_runner = DjangoTestSuiteRunner(verbosity=1)
from django_nose import NoseTestSuiteRunner

test_runner = NoseTestSuiteRunner()
failures = test_runner.run_tests(['friendface', ])
if failures:
    sys.exit(failures)
