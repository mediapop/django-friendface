from django.conf import settings
from django.contrib.auth.models import User
from better_facebook.models import FacebookUser

# Get the name of the AUTH profile so that we can check if the user
# has a relationship with facebook. Is there a neater way of doing this?
_lowercase_profile_name = settings.AUTH_PROFILE_MODULE.split(".")[1].lower()
_facebook_relation = '{0}__facebook'.format(_lowercase_profile_name)

class FacebookBackend(object):
    """
    Authenticate against a facebook_user object.
    """
    def authenticate(self, facebook_user):
        assert(isinstance(facebook_user, FacebookUser))
        try:
            return User.objects.get(**{_facebook_relation: facebook_user})
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None