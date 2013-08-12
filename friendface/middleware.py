from django.contrib.auth import authenticate, login, logout
from friendface.models import FacebookApplication
from django.middleware.csrf import _get_new_csrf_key
from friendface.models import FacebookUser


class P3PMiddleware(object):
    def process_response(self, request, response):
        response['P3P'] = (
            'CP="This is not a P3P policy! See http://www.google.com/support/'
            'accounts/bin/answer.py?hl=en&answer=151657 for more info."'
        )
        return response


class FacebookApplicationMiddleware(object):
    def process_request(self, request):
        try:
            application = FacebookApplication.get_for_request(request)
            setattr(request, 'facebook', application)
        except FacebookApplication.DoesNotExist:
            pass


class FacebookDecodingMiddleware(object):
    def process_request(self, request):
        #@todo This could use a middleware that finds the FacebookApplication
        # based on which application can decode signed_request
        signed_request = request.POST.get('signed_request')
        if hasattr(request, 'facebook') and signed_request:
            decoded = request.facebook.decode(signed_request) or {}
            setattr(request, 'FACEBOOK', decoded)
        else:
            setattr(request, 'FACEBOOK', {})


class DisableCsrfProtectionOnDecodedSignedRequest(object):
    def process_request(self, request):
        """
        If we are getting a POST that results in a decoded signed_request
        we shouldn't do CSRF protection. This is really so that we do not
        need to do @csrf_exempt on all views that interacts with Facebook.
        """
        if request.FACEBOOK:
            request.META["CSRF_COOKIE"] = _get_new_csrf_key()
            request.csrf_processing_done = True


class FacebookSignedRequestAuthenticationMiddleware(object):
    """If a signed_request has been decoded this will log that user in."""
    def process_request(self, request):
        # Safari doesn't set third party cookies, so we shouldn't authenticate
        # users that don't have cookies, as the logged in user won't be visible
        # in future AJAX calls.
        if not request.COOKIES:
            return

        if hasattr(request, 'FACEBOOK') and 'user_id' in request.FACEBOOK:
            user_id = request.FACEBOOK['user_id']
            app = request.facebook
            try:
                facebook_user = app.facebookuser_set.get(uid=user_id)
            except FacebookUser.DoesNotExist:
                return logout(request)
            else:
                authenticated_user = authenticate(facebook_user=facebook_user)
                if authenticated_user and authenticated_user.is_active:
                    login(request, authenticated_user)
