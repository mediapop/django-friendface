from django.contrib.auth import authenticate, login
from friendface.models import FacebookApplication, FacebookPage
from django.middleware.csrf import _get_new_csrf_key
from friendface.models import FacebookUser
from friendface.utils import memoize


class FacebookContext(object):
    def __init__(self, request):
        self.django_request = request

    @memoize
    def application(self):
        return FacebookApplication.get_for_request(self.request)

    @memoize
    def user(self):
        # If we have a user_id in the request:
        # 1. Attempt to get the user.
        # 2. If the user doesn't exist. Log the current user out.
        application = self.application()

        if (self.request() or {}).get('user_id'):
            user_id = self.request().get('user_id')
            try:
                user = application.facebookuser_set.get(uid=user_id)
            except FacebookUser.DoesNotExist:
                pass
            else:
                # This facebook user has a user already, log the current one
                # out.
                authenticated_user = authenticate(facebook_user=user)
                if authenticated_user and authenticated_user.is_active:
                    login(self.django_request, authenticated_user)

                return user

        return self.application().facebookuser_set.get(
            user=self.request.user
        )

    @memoize
    def request(self):
        request = self.django_request.POST.get('signed_request')
        if not request:
            return self.application().decode(request)


    @memoize
    def page(self):
        page_id = (self.request() or {}).get('page').get('id')
        if page_id:
            return FacebookPage.objects.get(pk=page_id)


class FacebookMiddleware(object):
    def process_request(self, request):
        setattr(request, 'facebook', FacebookContext(request))

        # Disable CSRF protection for requests originating from facebook.
        if request.facebook.request():
            request.facebook.META['CSRF_COOKIE'] = _get_new_csrf_key()
            request.csrf_processing_done = True

    def process_response(self, request, response):
        if 'P3P' in response:
            response['P3P'] = ("Nonsense https://support.google.com/accounts/"
                               "bin/answer.py?hl=en&answer=151657")
        return response