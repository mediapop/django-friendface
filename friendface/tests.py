# -*- encoding: utf-8 -*-
from django.contrib.auth.models import User
from django.views.generic import View
from facebook import GraphAPI
import os
from mock import patch
from django.http import HttpRequest
from django.test.testcases import TestCase
from friendface.models import FacebookApplication, FacebookAuthorization, \
    FacebookUser
import urllib
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from friendface.views import FacebookAppAuthMixin, FacebookPostAsGetMixin
from friendface.fixtures import FacebookApplicationFactory

TEST_USER = {
    'id': 12345678,
    'first_name': 'Kit',
    'last_name': 'Sunde',
    'email': 'foo@foo.com'
}


def old_fixture_equivalent():
    return FacebookApplicationFactory.create(
        id=1,
        name='foo',
        secret='bar',
        namespace='mhe',
        canvas_url='http://testserver/',
        secure_canvas_url='https://testserver/',
        link=('http://www.facebook.com/apps/application.php?'
              'id=382752368461014')
    )


class FacebookAuthorizedTestCase(TestCase):
    def setUp(self):
        old_fixture_equivalent()  # for old tests to work
        patcher = patch.object(FacebookAuthorization,
                               'get_access_token',
                               lambda a, b: u'☃')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(GraphAPI, 'get_object', lambda a, b: TEST_USER)
        patcher.start()
        self.addCleanup(patcher.stop)

        app = FacebookApplication.objects.get()
        self.auth = FacebookAuthorization.objects.create(application=app,
                                                         next='/',
                                                         scope='',
                                                         redirect_uri='')

    def test_creates_facebook_user_if_not_exists(self):
        self.assertEqual(FacebookUser.objects.count(), 0)
        self.client.get(self.auth.get_absolute_url())
        self.assertEqual(FacebookUser.objects.count(), 1)

    def test_creates_new_user_if_not_exists(self):
        self.assertEqual(User.objects.count(), 0)
        self.client.get(self.auth.get_absolute_url())
        self.assertEqual(User.objects.count(), 1)

    def test_creating_user_sets_details_from_facebook(self):
        self.client.get(self.auth.get_absolute_url())
        user = User.objects.get()
        facebook_user = FacebookUser.objects.get()
        self.assertEqual(user.email, facebook_user.email)
        self.assertEqual(user.first_name, facebook_user.first_name)
        self.assertEqual(user.last_name, facebook_user.last_name)


class FacebookApplicationTestCase(TestCase):
    def setUp(self):
        old_fixture_equivalent()  # for old tests to work

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


class FacebookPostAsGetMixinTestCase(TestCase):
    def setUp(self):
        old_fixture_equivalent()  # for old tests to work
        self.request = HttpRequest()
        self.request.method = 'post'
        self.request.META = {'SERVER_NAME': 'localserver', 'SERVER_PORT': 80}
        self.request.path = '/same-url/'
        setattr(self.request, 'FACEBOOK', {'true': 'value'})
        setattr(self.request, 'facebook', FacebookApplication.objects.get())
        self.base_url = reverse(
            'friendface.views.authorize',
            kwargs={'application_id': self.request.facebook.id})

    def test_regular_post(self):
        setattr(self.request, 'FACEBOOK', {})

        class TestView(FacebookPostAsGetMixin, View):
            def get(self, request, *args, **kwargs):
                return False

            def post(self, request, *args, **kwargs):
                return True

        self.assertTrue(TestView().dispatch(self.request))

    def test_facebook_request(self):
        class TestView(FacebookPostAsGetMixin, View):
            def get(self, request, *args, **kwargs):
                return True

            def post(self, request, *args, **kwargs):
                return False

        self.assertTrue(TestView().dispatch(self.request))


class FacebookAuthorizationMixinTestCase(TestCase):
    def setUp(self):
        old_fixture_equivalent()  # for old tests to work
        self.request = HttpRequest()
        self.request.META = {'SERVER_NAME': 'localserver', 'SERVER_PORT': 80}
        self.request.path = '/same-url/'
        setattr(self.request, 'user', AnonymousUser())
        setattr(self.request, 'FACEBOOK', {})
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
    def setUp(self):
        old_fixture_equivalent()  # for old tests to work
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


class ChannelViewTest(TestCase):
    URL = reverse('friendface.views.channel')

    def test_set_max_age(self):
        res = self.client.get(self.URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get('Cache-Control'),
                         'public, max-age=31536000')


class FacebookApplicationInstallRedirectViewTest(TestCase):
    def setUp(self):
        self.app = FacebookApplicationFactory.create()

    def test_should_redirect_with_application_id_given(self):
        res = self.client.get(reverse('friendface.views.install',
                                      kwargs=dict(application_id=self.app.id)))
        self.assertEqual(res.status_code, 302)
        self.assertTrue('facebook.com/dialog/pagetab' in res.get('Location'))
        self.assertTrue('app_id={0}'.format(self.app.pk)
                        in res.get('Location'))

    def test_should_raise_400_on_invalid_app_id(self):
        res = self.client.get(reverse('friendface.views.install',
                                      kwargs=dict(application_id=1234)))
        self.assertEqual(res.status_code, 400)
        self.assertTrue('No application' in res.content)

    def test_no_configured_app_should_raise_400(self):
        res = self.client.get(reverse('friendface.views.install'))
        self.assertEqual(res.status_code, 400)
        self.assertTrue('No app configured on this URL' in res.content)

    def test_app_configured_and_no_application_id_given_should_redirect(self):
        url = reverse('friendface.views.install')
        app = FacebookApplicationFactory.create(
            website_url=url.replace('install/', '')
        )
        res = self.client.get(url)

        self.assertEqual(res.status_code, 302)
        self.assertTrue('app_id={0}'.format(app.pk) in res.get('Location'))
