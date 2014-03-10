from django.conf import settings

try:
    from django.contrib.auth.models import AbstractUser

    if settings.AUTH_USER_MODEL.endswith('CustomUser'):
        class CustomUser(AbstractUser):
            pass
except ImportError:
    pass
