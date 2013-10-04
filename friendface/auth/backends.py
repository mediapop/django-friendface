from friendface.models import FacebookUser
from friendface.utils import get_user_model

User = get_user_model()


class FacebookBackend(object):
    """
    Authenticate against a facebook_user object.
    """
    def authenticate(self, facebook_user):
        assert(isinstance(facebook_user, FacebookUser))
        return facebook_user.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
