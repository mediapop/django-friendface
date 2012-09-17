from friendface.models import FacebookApplication

class FacebookApplicationMiddleware(object):
    def process_request(self, request):
        # This is admittedly a rather strange looking.. lookup.
        # What we need to do is find out if the applications canvas_url is the
        # start of the URL we are currently on. Once that has been established
        # we also need to find out which canvas_url is longer to find out
        # which is the closer match.
        current_url = request.build_absolute_uri()
        field = 'secure_canvas_url' if request.is_secure() else 'canvas_url'

        apps = FacebookApplication.objects.extra(
            select={'{0}_length'.format(field): 'Length({0})'.format(field)},
            where=["%s LIKE CONCAT({0}, %s)".format(field)],
            params=[current_url, '%']).order_by('-{0}_length'.format(field))

        try:
            setattr(request, 'facebook', apps[0])
        except IndexError:
            pass