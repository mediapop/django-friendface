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

        base_extra_args = {
            'select': {'{0}_length'.format(field): 'Length({0})'.format(field)},
            'params': [current_url, '%']
        }

        apps = FacebookApplication.objects.order_by('-{0}_length'.format(field))

        try:
            extra_args = base_extra_args.copy()
            extra_args['where'] = ["%s LIKE CONCAT({0}, %s)".format(field)]
            apps = list(apps.extra(**extra_args))
        except DatabaseError as e:
            # SQLite3 cannot do CONCAT so we'll manually filter the list.
            # Is there a way to dect the datbase backend so we don't have to
            # try to connect and then recover?
            if e.message != 'no such function: CONCAT':
                raise

            apps = filter(lambda a: getattr(a, field).startswith(field),
                          apps.extra(**base_extra_args))

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