from django.contrib.auth.models import User
from friendface.models import FacebookUser


class FacebookBackend(object):
    """
    Authenticate against a facebook_user object.
    """
    def authenticate(self, facebook_user):
        assert(isinstance(facebook_user, FacebookUser))
        try:
            return User.objects.get(facebook_user=facebook_user)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
