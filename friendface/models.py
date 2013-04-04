import datetime
import logging
import urllib
import urllib2
import urlparse

from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone

from facebook import parse_signed_request
import facebook
import requests

from model_utils.fields import MonitorField

logger = logging.getLogger('friendface')


class FacebookRequestMixin(object):
    def request(self, path, args=None, post_args=None):
        graph = facebook.GraphAPI(self.access_token)
        return graph.request(path, args, post_args)

    def fql(self, query):
        params = {'access_token': self.access_token, 'q': query}
        response = requests.get("https://graph.facebook.com/fql", params=params)
        return response.json


class AccessTokenMixin(models.Model):
    access_token = models.CharField(max_length=128,
                                    null=True,
                                    editable=False,
                                    help_text="These are valid for 90 days.")
    access_token_updated_at = MonitorField(
        monitor='access_token',
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    @property
    def access_token_valid(self):
        return (
            self.access_token_updated_at + datetime.timedelta(days=90)
        ) > timezone.now()


class FacebookUser(AccessTokenMixin, models.Model, FacebookRequestMixin):
    created = models.DateTimeField(auto_now_add=True)
    uid = models.BigIntegerField()
    application = models.ForeignKey('FacebookApplication')

    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    timezone = models.IntegerField(max_length=100, null=True, blank=True)
    religion = models.CharField(max_length=100, null=True, blank=True)

    locale = models.CharField(max_length=8, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)

    email = models.EmailField(blank=True,
                              null=True)
    gender = models.CharField(max_length=8, null=True, blank=True)

    pages = models.ManyToManyField(
        'FacebookPage', through='PageAdmin',
        help_text='The pages this user is admin for'
    )

    class Meta:
        unique_together = ('uid', 'application')

    def get_picture_url(self):
        return "https://graph.facebook.com/{0}/picture".format(self.uid)

    def has_liked(self, target):
        """ target must either be a URL or a facebook id. """
        try:
            response = self.request('/me/likes/%d' % int(target))
        except ValueError:
            response = self.fql(
                'SELECT url '
                'FROM url_like '
                'WHERE user_id = me() '
                '   AND strpos(url, "%s") = 0' % target)
        return not not response['data']

    def full_name(self):
        if not self.first_name and not self.last_name:
            return u"Unknown"
        return u"{0} {1}".format(self.first_name, self.last_name)

    def send_notification(self, message, app_access_token=None, href=None,
                          ref=None):
        if app_access_token is None:
            app_access_token = self.application.access_token

        r = requests.post(
            'https://graph.facebook.com/{0}/notifications'.format(self.uid),
            params={
                'access_token': app_access_token,
                'href': href,
                'template': message,
                'ref': ref
            })

        return r.json

    def get_long_lived_access_token(self):
        '''
        format of response: access_token=<token>&timestamp=<timestamp>
        Only it doesn't give the timestamp every time.
        '''
        app = self.application
        return self.request('/oauth/access_token', args=dict(
            client_id=app.id,
            client_secret=app.secret,
            grant_type='fb_exchange_token',
            fb_exchange_token=self.access_token
        )).split('&')[0].replace('access_token=', '')

    def __unicode__(self):
        return self.full_name()


class FacebookAuthorization(models.Model):
    application = models.ForeignKey('FacebookApplication')
    # @todo It might be better if this was a M2M choice field, since then we
    # could easily catch mistakes in asking for permissions.
    scope = models.CharField(max_length=255)
    redirect_uri = models.URLField(help_text="""We need this to talk to
    Facebook in the authorized step of authentication.""", blank=True)
    next = models.CharField(max_length=255)

    def get_access_token(self, code):
        query = urllib.urlencode({'client_id': self.application_id,
                                  'redirect_uri': self.redirect_uri,
                                  'client_secret': self.application.secret,
                                  'code': code})

        url = 'https://graph.facebook.com/oauth/access_token?{0}'.format(query)

        auth_response = urllib2.urlopen(url).read()
        parsed_response = urlparse.parse_qs(auth_response)
        return parsed_response['access_token']

    def get_absolute_url(self):
        return reverse('friendface.views.authorized', kwargs={
            'authorization_id': self.id
        })

    def get_authorized_url(self):
        return reverse('friendface.views.authorized',
                       kwargs={'authorization_id': self.id})

    def get_facebook_authorize_url(self):
        query = urllib.urlencode({
            'client_id': self.application_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope})

        facebook_url = "https://graph.facebook.com/oauth/authorize"
        return "{0}?{1}".format(facebook_url, query)


class FacebookApplication(AccessTokenMixin, models.Model, FacebookRequestMixin):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=32,
                            null=True,
                            blank=True)
    secret = models.CharField(max_length=32,
                              help_text='Application secret')
    default_scope = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default scope i.e. 'user_likes,email'")
    url = models.URLField(
        help_text="""A FacebookApplication has a URL. People are normally sent
        here by clicking the application icon, or via invites etc.""",
        blank=True,
        null=True)
    namespace = models.CharField(max_length=20,
                                 blank=True,
                                 null=True)

    description = models.TextField(blank=True, null=True)

    # @todo add all options as choices
    category = models.CharField(blank=True, null=True, max_length=23)
    subcategory = models.CharField(blank=True, null=True, max_length=15)

    company = models.CharField(blank=True, null=True, max_length=60)
    icon_url = models.URLField(blank=True, null=True)

    link = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    daily_active_users = models.BigIntegerField(blank=True, null=True)
    weekly_active_users = models.BigIntegerField(blank=True, null=True)
    monthly_active_users = models.BigIntegerField(blank=True, null=True)
    auth_dialog_data_help_url = models.URLField(blank=True, null=True)
    auth_dialog_headline = models.CharField(max_length=32,
                                            blank=True,
                                            null=True)
    auth_dialog_perms_explanation = models.TextField(blank=True, null=True)
    auth_referral_default_activity_privacy = models.CharField(choices=(
        ('ALL_FRIENDS', 'ALL_FRIENDS'),
        ('SELF', 'SELF'),
        ('EVERYONE', 'EVERYONE'),
        ('NONE', 'NONE')),
        max_length=11,
        blank=True,
        null=True)
    auth_referral_enabled = models.NullBooleanField(blank=True, null=True)
    auth_referral_extended_perms = models.CharField(max_length=5,
                                                    blank=True,
                                                    null=True)
    canvas_fluid_height = models.NullBooleanField(blank=True, null=True)
    canvas_fluid_width = models.NullBooleanField(blank=True, null=True)
    canvas_url = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    created_time = models.BigIntegerField(blank=True, null=True)
    deauth_callback_url = models.URLField(blank=True, null=True)
    iphone_app_store_id = models.IntegerField(blank=True, null=True)
    hosting_url = models.URLField(blank=True, null=True)
    mobile_web_url = models.URLField(blank=True, null=True)
    page_tab_default_name = models.TextField(blank=True, null=True)

    page_tab_url = models.URLField(blank=True, null=True)
    privacy_policy_url = models.URLField(blank=True, null=True)
    secure_canvas_url = models.URLField(blank=True, null=True)
    secure_page_tab_url = models.URLField(blank=True, null=True)
    social_discovery = models.NullBooleanField(blank=True, null=True)
    terms_of_service_url = models.URLField(blank=True, null=True)
    user_support_email = models.EmailField(blank=True, null=True)
    user_support_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def url(self):
        return self.build_canvas_url()

    @classmethod
    def get_for_request(cls, request):
        """Find the application responsible for the request.
        :param request: HttpRequest to check against
        :returns: py:class:`FacebookApplication`
        :raises: py:class:`FacebookApplication.DoesNotExist` if there's no
        match.
        """
        # Should we really lookup on request rather than URL? If we get a
        # request we can figure out if we need to check canvas_url or
        # website_url based on signed_request, but that might just be a
        # silly micro optimization.
        # @todo Make this not grow linearly with the DB.
        # @todo Filter on app_domains when we have those in the app.
        # This used to be a giant DB lookup but it was incredibly painful to
        # debug and it didn't support protocol-independent
        # (http, https) lookups.
        # Now we've moved the work from the database here. It's possible that
        # to move it back in a simplified form if we kept a separate
        # URL matching table that has website_url, domain, canvas_url etc.
        # without the protocol and with the foreign key back to the app.
        current_url = urlparse.urlparse(request.build_absolute_uri())
        is_secure = request.is_secure()
        canvas = 'secure_canvas_url' if is_secure else 'canvas_url'
        page_tab = 'secure_page_tab_url' if is_secure else 'page_tab_url'

        match = None
        longest_match = None

        for app in FacebookApplication.objects.all():
            match_urls = (app.website_url, app.mobile_web_url,
                          getattr(app, canvas), getattr(app, page_tab))

            for url in match_urls:
                if not url: continue
                match_path = urlparse.urlparse(url).path

                if current_url.path.startswith(match_path):
                    if len(match_path) > longest_match:
                        longest_match = len(match_path)
                        match = app

        if not match: raise FacebookApplication.DoesNotExist

        return match

    def build_canvas_url(self, location=None):
        """Takes the URL relative to Django and turns it into a URL
        relative this facebook apps canvas page."""
        if not self.canvas_url: return None
        if location is None:
            return "https://apps.facebook.com/{0}/".format(self.namespace or
                                                           self.id)
        canvas_path = urlparse.urlparse(self.canvas_url).path
        assert location.startswith(canvas_path), "The application path %s " \
            "doesn't is not the start of the location path so no canvas url " \
            "can be derived."
        clipped_path = location[len(canvas_path):]
        return urlparse.urljoin(self.url, clipped_path)

    def get_access_token(self):
        response = requests.get(
            "https://graph.facebook.com/oauth/access_token",
            params={
                'client_id': self.id,
                'client_secret': self.secret,
                'grant_type': 'client_credentials'
            })

        return urlparse.parse_qs(response.text).get('access_token')[0]

    def save(self, *args, **kwargs):
        self.access_token = self.get_access_token()
        graph = facebook.GraphAPI(access_token=self.get_access_token())
        # @todo This should be a whitelist rather than a blacklist.
        exclude_fields = ('secret', 'default_scope', 'access_token', 'id')
        fields = ",".join(field.name
                          for field in FacebookApplication._meta.fields
                          if field.name not in exclude_fields)

        # Facebook gives us a limited amount of fields by default, we need
        # to explicitly request the additoinal ones.
        app_data = graph.request(unicode(self.id), {'fields': fields})

        for key, value in app_data.items():
            setattr(self, key, value)
        super(FacebookApplication, self).save(*args, **kwargs)

    def scrape(self, obj):
        # Tell facebook to crawl the URL so it both has the data already on
        # first share and we clear all of those debug ones.
        data = {
            'id': "{0}{1}".format(self.url, obj.get_absolute_url()),
            'scrape': 'true'
        }
        return urllib2.urlopen('https://graph.facebook.com/',
                               urllib.urlencode(data)).read()

    def get_absolute_url(self):
        return self.url

    def get_authorize_url(self, next=None):
        authorize_url = reverse('friendface.views.authorize',
                                kwargs={'application_id': self.id})
        if not next is None:
            authorize_url += "?" + urllib.urlencode({"next": next})
        return authorize_url

    def decode(self, signed_request):
        return parse_signed_request(signed_request, str(self.secret))

    def send_notification(self, user, message, href=None, ref=None):
        return user.send_notification(message=message,
                                      app_access_token=self.access_token,
                                      href=href,
                                      ref=ref)


class FacebookTab(models.Model):
    """In this case we should only ever have one FacebookTab, but I'm setting
    it up here either way."""
    application = models.ForeignKey('FacebookApplication')
    page = models.ForeignKey('FacebookPage')

    class Meta:
        get_latest_by = 'id'

    def get_absolute_url(self):
        if self.page.name_space:
            return "{0}app_{1}".format(self.page.get_absolute_url(),
                                       self.application_id)
        return "{0}?sk=app_{1}".format(self.page.get_absolute_url(),
                                       self.application_id)

    def __unicode__(self):
        return "{0} on {1}".format(self.application, self.page)


class FacebookInvitation(models.Model):
    request_id = models.BigIntegerField()
    created = models.DateTimeField(auto_now_add=True,
                                   editable=False)
    application = models.ForeignKey(FacebookApplication)
    sender = models.ForeignKey(FacebookUser,
                               related_name='facebookinvitations_sent')
    receiver = models.ForeignKey(FacebookUser,
                                 related_name='facebookinvitations_received')
    accepted = models.DateTimeField(null=True)
    next = models.URLField(help_text=('By default the user gets sent to the '
                                      'application canvas page.'))

    @classmethod
    def create_with_receiver(cls, receiver, request_id, application, sender,
                             **kwargs):
        '''
        Arguments:
          receiver: The Facebook UID of the person who receives the request
          request_id: Facebooks request id
          application: THe Facebook application that the request is for
          sender: the FacebookUser who sent the request

        Optional arguments:
          next: The URL the user will be forcefully be redirected to after
                the invitation has been accepted.
        '''
        receiver, _ = FacebookUser.objects.get_or_create(
            uid=receiver,
            application=application
        )

        return FacebookInvitation.objects.create(
            request_id=request_id,
            receiver=receiver,
            sender=sender,
            application=application,
            **kwargs
        )

    class Meta:
        unique_together = ('request_id', 'receiver')

    def __unicode__(self):
        return unicode(self.request_id)


class FacebookPage(models.Model):
    """There should only ever be one FacebookPage"""
    id = models.BigIntegerField(primary_key=True,
                                help_text="The id of the FacebookPage")
    name = models.CharField(max_length=100,
                            help_text="The name of the page",
                            null=True,
                            blank=True)
    link = models.URLField(blank=True,
                           null=True)
    likes = models.BigIntegerField(blank=True,
                                   null=True)
    talking_about_count = models.BigIntegerField(blank=True,
                                                 null=True)
    category = models.CharField(max_length=32, blank=True, null=True)
    name_space = models.CharField(
        help_text="A FacebookPage can have a name-space which is in the URL",
        max_length=20,
        blank=True,
        null=True)
    is_published = models.NullBooleanField(blank=True,
                                           null=True)
    users = models.ManyToManyField(
        FacebookUser, through='PageAdmin',
        help_text='The Facebook Users that are admins for this page'
    )

    def save(self, *args, **kwargs):
        graph = facebook.GraphAPI()
        page_data = graph.request(unicode(self.id))
        for key, value in page_data.items():
            setattr(self, key, value)
        super(FacebookPage, self).save(*args, **kwargs)

    def get_absolute_url(self):
        base_url = "https://www.facebook.com/"
        if self.name_space:
            return "{0}{1}/".format(base_url, self.name_space)
        return "{0}pages/{1}/{2}".format(base_url, slugify(self.name), self.id)

    def __unicode__(self):
        return self.name


class PageAdmin(AccessTokenMixin, models.Model, FacebookRequestMixin):
    user = models.ForeignKey(FacebookUser, related_name='+')
    page = models.ForeignKey(FacebookPage, related_name='+')

    updated_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()

        return super(PageAdmin, self).save(*args, **kwargs)

    @classmethod
    def create_for_user(cls, user):
        '''
        Given a FacebookUser instance with manage_pages permissions this will
        query Facebook for all pages this user has access to.

        FacebookPage instances will be created if needed and access_tokens will
        be updated if it has changed.

        Also all pages in the database that has not been queried will be
        deleted.
        '''
        pages = user.request(path='/me/accounts')
        if not 'data' in pages:
            return False

        page_ids = []

        for page in pages['data']:
            try:
                fb_page, new = FacebookPage.objects.get_or_create(
                    id=page['id']
                )
            except facebook.GraphAPIError as e:
                logger.error('Error creating FacebookPage "%s" - %s: ',
                             page['id'], e.message, extra={'stack': True})
            else:
                page_ids.append(page['id'])
                obj, new = cls.objects.get_or_create(
                    user=user,
                    page=fb_page,
                    defaults={
                        'access_token': page['access_token']
                    })

                if not new and obj.access_token != page['access_token']:
                    obj.access_token = page['access_token']
                    obj.save()

            if len(page_ids) > 0:
                (cls.objects.filter(user=user)
                 .exclude(page_id__in=page_ids)
                 .delete())

        return True
