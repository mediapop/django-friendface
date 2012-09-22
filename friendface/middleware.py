from django.db import connection
from friendface.models import FacebookApplication
from django.db.utils import DatabaseError

class FacebookApplicationMiddleware(object):
    def process_request(self, request):
        # This is admittedly a rather strange looking.. lookup.
        # What we need to do is find out if the applications canvas_url is the
        # start of the URL we are currently on. Once that has been established
        # we also need to find out which canvas_url is longer to find out
        # which is the closer match.
        current_url = request.build_absolute_uri()
        field = 'secure_canvas_url' if request.is_secure() else 'canvas_url'

        extra_args = {
            'select': {'{0}_length'.format(field): 'Length({0})'.format(field)},
            'params': [current_url, '%']
        }
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            # MySQL doesn't support ANSI SQL concat via || without setting
            # PIPES_AS_CONCAT. Can we detect the PIPES_AS_CONCAT setting?
            # Also: http://dev.mysql.com/doc/refman/5.6/en/ansi-mode.html
            extra_args['where'] = ["%s LIKE CONCAT({0}, %s)".format(field)]
        else:
            extra_args['where'] = ["%s LIKE {0} || %s".format(field)]

        apps = FacebookApplication.objects.extra(**extra_args)\
        .order_by('-{0}_length'.format(field))

        try:
            setattr(request, 'facebook', apps[0])
        except IndexError:
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