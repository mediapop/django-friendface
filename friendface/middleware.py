from django.contrib.auth import authenticate, login
from friendface.models import FacebookApplication


class P3PMiddleware(object):
    def process_response(self, request, response):
        response['P3P'] = ("Nonsense https://support.google.com/accounts/bin/"
                           "answer.py?hl=en&answer=151657")
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
        # based on which application cand ecode signed_request
        #@todo Handle cases where decoding the signed_request isn't possible
        signed_request = request.POST.get('signed_request')
        if hasattr(request, 'facebook') and signed_request:
            decoded = request.facebook.decode(signed_request)
            setattr(request, 'FACEBOOK', decoded)
        else:
            setattr(request, 'FACEBOOK', {})


class FacebookSignedRequestAuthenticationMiddleware(object):
    """If a signed_request has been decoded this will log that user in."""
    def process_request(self, request):
        if hasattr(request, 'FACEBOOK') and 'user_id' in request.FACEBOOK:
            user_id = request.FACEBOOK['user_id']
            facebook_user = request.facebook.facebookuser_set.get(uid=user_id)
            authenticated_user = authenticate(facebook_user=facebook_user)
            if authenticated_user and authenticated_user.is_active:
                login(request, authenticated_user)
