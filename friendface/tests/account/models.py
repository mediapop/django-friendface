try:
    from django.contrib.auth.models import AbstractUser

    class CustomUser(AbstractUser):
        pass
except ImportError:
    pass
