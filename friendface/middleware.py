from friendface.models import FacebookApplication

class FacebookApplicationMiddleware(object):
    def process_request(self, request):
        current_url = request.build_absolute_uri()
        match_url = "^" + current_url.replace('http://', 'https://')
        # This is admittedly a rather strange looking.. lookup.
        # What we need to do is find out if the applications canvas_url is the
        # start of the URL we are currently on. Once that has been established
        # we also need to find out which canvas_url is longer to find out
        # which is the closer match.

        apps = FacebookApplication.objects.extra(
            select={'canvas_url_length': 'Length(canvas_url)'},
            where=["%s LIKE CONCAT(canvas_url, %s)"],
            params=[match_url,'%']).order_by('-canvas_url_length')
        try:
            setattr(request, 'facebook', apps[0])
        except IndexError:
            pass