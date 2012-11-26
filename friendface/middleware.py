from django.contrib.auth import authenticate, login
from django.db import connection
import re
from friendface.models import FacebookApplication

class P3PMiddleware(object):
    def process_response(self, request, response):
        response['P3P'] = "Nonsense https://support.google.com/accounts/bin/answer.py?hl=en&answer=151657"
        return response

class FacebookApplicationMiddleware(object):
    _match_non_ansi_concat = re.compile('CONCAT\((.+),(.+)\)')

    def _find_applications(self, request):
        # This rather awkward query finds application by finding all matching
        # applications and then selecting the ones with the longest match
        # Attempting to turn this into a single query with the ORM is left as a
        # futile exercise to the reader
        current_url = request.build_absolute_uri()
        canvas = 'secure_canvas_url' if request.is_secure() else 'canvas_url'
        page_tab = 'secure_page_tab_url' if request.is_secure() else 'page_tab_url'

        # We don't need to query for  website_url or mobile_web_url if there's
        # a signed_request present
        if request.POST.get('signed_request'):
            additional_lookups = """
                UNION ALL
                SELECT *, LENGTH(website_url) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT(website_url, %s)
                UNION ALL
                SELECT *, LENGTH(mobile_web_url) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT(website_url, %s)"""
            additional_length_match = """
                UNION ALL
                SELECT LENGTH(website_url) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT(website_url, %s)
                UNION ALL
                SELECT LENGTH(mobile_web_url) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT(website_url, %s)"""
        else:
            additional_lookups = additional_length_match = ''

        query = """
            SELECT * FROM (
              SELECT *, LENGTH({page_tab_field}) AS MatchLen
              FROM friendface_facebookapplication
              WHERE %s LIKE CONCAT({page_tab_field}, %s)
              UNION ALL
              SELECT *, LENGTH({canvas_field}) AS MatchLen
              FROM friendface_facebookapplication
              WHERE %s LIKE CONCAT({canvas_field}, %s)
              {additional_lookups}
            ) AS matches
            WHERE MatchLen = (
              -- Find the maximum length.
              SELECT MAX(MatchLen) FROM (
                SELECT LENGTH({page_tab_field}) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT({page_tab_field}, %s)
                UNION ALL
                SELECT LENGTH({canvas_field}) AS MatchLen
                FROM friendface_facebookapplication
                WHERE %s LIKE CONCAT({canvas_field}, %s)
                {additional_length_match}
              ) as LengthMatch);
        """.format(additional_lookups=additional_lookups,
                   additional_length_match=additional_length_match,
                   canvas_field=canvas,
                   page_tab_field=page_tab)

        # MySQL doesn't support ANSI SQL concat via || without setting
        # PIPES_AS_CONCAT. Can we detect the PIPES_AS_CONCAT setting?
        # See: http://dev.mysql.com/doc/refman/5.6/en/ansi-mode.html
        if not connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            query = self._match_non_ansi_concat.sub("\\1 || \\2", query)

        # The Python SQLite adapter doesn't allow %(named_param)s for raw
        # queries, so to work around that just use %s and replace the old
        # fashioned way.
        parameters = [current_url, '%', ] * 4
        if additional_lookups and additional_length_match:
            parameters = parameters + ([current_url, '%'] * 4)

        return FacebookApplication.objects.raw(query, parameters)



    def process_request(self, request):
        # We discover the FacebookApplication relevant to our URL by url
        # matching the applications settings.
        applications = self._find_applications(request)

        try:
            setattr(request, 'facebook', applications[0])
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


class FacebookSignedRequestAuthenticationMiddleware(object):
    """If a signed_request has been decoded this will log that user in."""
    def process_request(self, request):
        if hasattr(request, 'FACEBOOK') and 'user_id' in request.FACEBOOK:
            user_id = request.FACEBOOK['user_id']
            facebook_user = request.facebook.facebookuser_set.get(uid=user_id)
            authenticated_user = authenticate(facebook_user=facebook_user)
            if authenticated_user and authenticated_user.is_active:
                login(request, authenticated_user)