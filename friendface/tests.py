import urllib
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
import os
from django.http import HttpRequest
from django.test.testcases import TestCase
from friendface.models import FacebookApplication
from friendface.views import FacebookAppAuthMixin


class FacebookApplicationTestCase(TestCase):
    fixtures = ["application.json"]

    def test_authorize_url(self):
        app = FacebookApplication.objects.get()
        self.assertEqual(app.facebookauthorization_set.count(), 0)
        response = self.client.get(path=app.get_authorize_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.facebookauthorization_set.count(), 1)

    def test_authorize_url_next(self):
        app = FacebookApplication.objects.get()
        self.assertEqual(app.facebookauthorization_set.count(), 0)
        next = 'http://www.google.com'
        self.client.get(path=app.get_authorize_url(next))
        auth = app.facebookauthorization_set.get()
        self.assertEqual(next, auth.next)

    def test_build_canvas_url(self):
        app = FacebookApplication.objects.get()
        self.assertEqual("https://apps.facebook.com/%s/" % app.namespace,
                         app.build_canvas_url())

    def test_build_non_namespace_canvas_url(self):
        app = FacebookApplication.objects.get()
        app.namespace = None
        self.assertEqual("https://apps.facebook.com/%s/" % app.id,
                         app.build_canvas_url())


class FacebookAuthorizationMixinTestCase(TestCase):
    fixtures = ["application.json"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.META = {'SERVER_NAME': 'localserver', 'SERVER_PORT': 80}
        self.request.path = '/same-url/'
        setattr(self.request,'user', AnonymousUser())
        setattr(self.request,'FACEBOOK', {})
        setattr(self.request, 'facebook', FacebookApplication.objects.get())
        self.base_url = reverse(
            'friendface.views.authorize',
            kwargs={'application_id': self.request.facebook.id})

    def test_anonymous_users_get_authenticated(self):
        response = FacebookAppAuthMixin().dispatch(self.request)
        setattr(response, 'client', self.client)
        target = self.base_url + "?" + urllib.urlencode({
            'next': 'http://localserver/same-url/'})
        self.assertEqual(response._headers['location'][1], target)

    def test_auth_return_to_same_url(self):
        response = FacebookAppAuthMixin().dispatch(self.request)
        setattr(response, 'client', self.client)
        target = self.base_url + "?" + urllib.urlencode({
            'next': 'http://localserver/same-url/'})
        self.assertEqual(response._headers['location'][1], target)

    def test_auth_on_facebook_return_to_canvas_url(self):
        self.request.FACEBOOK['not'] = 'false'
        response = FacebookAppAuthMixin().dispatch(self.request)
        setattr(response, 'client', self.client)
        target = self.base_url + "?" + urllib.urlencode({
            'next': 'https://apps.facebook.com/mhe/same-url/'})
        self.assertEqual(response._headers['location'][1], target)


class environment:
    """
    Helper for setting environmental variables, merges. Usages:
    with environment({'HTTPS': 'off'}):
       pass
    """
    def __init__(self, envs):
        self.envs = envs

    def __enter__(self):
        self.old = os.environ
        os.environ = dict(os.environ, **self.envs)

    def __exit__(self, type, value, traceback):
        os.environ = self.old


class FacebookApplicationMatchingTestCase(TestCase):
    fixtures = ["application.json"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.path = '/foo'
        self.request.META = {'SERVER_NAME': 'www.foo.com', 'SERVER_PORT': 80}

    def test_get_for_request_matches_canvas_url(self):
        with environment({'HTTPS': 'off'}):
            app_url = 'http://www.foo.com/'
            self.request.POST = {'signed_request': 'asdf'}
            FacebookApplication.objects.update(canvas_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_canvas_url(self):
        with environment({'HTTPS': 'on'}):
            app_url = 'https://www.foo.com/'
            self.request.POST = {'signed_request': 'asdf'}

            FacebookApplication.objects.update(secure_canvas_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_page_tab_url(self):
        with environment({'HTTPS': 'off'}):
            app_url = 'http://www.foo.com/'
            self.request.POST = {'signed_request': 'asdf'}
            FacebookApplication.objects.update(page_tab_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_page_tab_url(self):
        with environment({'HTTPS': 'on'}):
            app_url = 'https://www.foo.com/'
            self.request.POST = {'signed_request': 'asdf'}

            FacebookApplication.objects.update(secure_page_tab_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_website_url(self):
        with environment({'HTTPS': 'on'}):
            app_url = 'https://www.foo.com/'

            FacebookApplication.objects.update(website_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_mobile_url(self):
        with environment({'HTTPS': 'on'}):
            app_url = 'https://www.foo.com/'

            FacebookApplication.objects.update(mobile_web_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_canvas_url_with_no_signed_request(self):
        with environment({'HTTPS': 'off'}):
            app_url = 'http://www.foo.com/'
            self.request.POST = {'other_data': 'asdf'}
            FacebookApplication.objects.update(canvas_url=app_url)
            application = FacebookApplication.get_for_request(self.request)
            self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_raises_exception_on_no_match(self):
        FacebookApplication.objects.update(canvas_url='foo',
                                           secure_canvas_url='foo')
        with self.assertRaises(FacebookApplication.DoesNotExist):
            FacebookApplication.get_for_request(self.request)
