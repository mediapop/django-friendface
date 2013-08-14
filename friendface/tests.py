# -*- encoding: utf-8 -*-
import os
import urllib
import unittest

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest, HttpResponse
from django.test.testcases import TestCase
from django.views.generic import View

from facebook import GraphAPI
from mock import patch
from testfixtures import LogCapture

from friendface import tasks
from friendface.fixtures import (create_user, FacebookApplicationFactory,
                                 FacebookInvitationFactory, FacebookPageFactory)
from friendface.models import (FacebookApplication, FacebookAuthorization,
                               FacebookUser, FacebookInvitation)
from friendface.shortcuts import rescrape_url, ScrapingError
from friendface.views import FacebookAppAuthMixin, FacebookPostAsGetMixin

# If a response for requests needs to be faked, add on and use this
class FakeResponse(object):
    def __init__(self, status_code, json=None):
        self.status_code = status_code
        self._json = json

    def json(self):
        return self._json


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


class FacebookPageTest(TestCase):
    def setUp(self):
        self.page = FacebookPageFactory.build()

    def test_default_unicode_is_id(self):
        self.assertEqual(unicode(self.page), unicode(self.page.id))

    def test_unicode_name(self):
        self.page.name = 'pancakes'
        self.assertEqual(unicode(self.page), unicode(self.page.name))


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

    def test_display_page_when_facebook_user_agent(self):
        """Should let through anyway if the user agent is the scraper"""
        self.request.META['HTTP_USER_AGENT'] = (
            'facebookexternalhit/1.1 (+http://www.facebook.com/'
            'externalhit_uatext.php)'
        )
        self.request.method = 'get'
        class TestView(FacebookAppAuthMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse('OK')

        response = TestView().dispatch(self.request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('OK', response.content)


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
                                           secure_canvas_url='foo',
                                           website_url='/dashboard/')
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
        self.app = FacebookApplicationFactory.create(website_url='/dashboard/')

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


@patch.object(FacebookApplication, 'request')
class FacebookInvitationMixinTest(TestCase):
    URL = reverse('friendface.views.invitation_handler')

    def setUp(self):
        self.fb_user, self.user, self.app = create_user(True)
        self.invitation = FacebookInvitationFactory.create(
            application=self.app,
            receiver=self.fb_user
        )

    def test_vanilla_authed_user_accept_invitation_that_doesnt_exist(self, _):
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        request_id = '123456'
        res = self.client.get(self.URL, {'request_ids': request_id})

        self.assertEqual(res.status_code, 200)
        self.assertRaises(FacebookInvitation.DoesNotExist,
                          FacebookInvitation.objects.get,
                          request_id=request_id)

    def test_authed_user_with_no_request_ids(self, _):
        '''Should not do a redirect or anything, just accept on'''
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        res = self.client.get(self.URL)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(FacebookInvitation.objects
                         .exclude(accepted=None)
                         .exists())

    def test_vanilla_authed_user_accept_invitation(self, _):
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        res = self.client.get(self.URL, {
            'request_ids': self.invitation.request_id
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(FacebookInvitation.objects
                        .get(request_id=self.invitation.request_id)
                        .accepted)

    def test_vanilla_authed_accept_calls_handle_invitation(self, _):
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        res = self.client.get(self.URL, {
            'request_ids': self.invitation.request_id
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue('Handle invitation called' in res.content, res.content)
        self.assertTrue(FacebookInvitation.objects
                        .get(request_id=self.invitation.request_id)
                        .accepted)

    def test_accept_invitation_delete_from_facebook(self, mocked):
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        self.client.get(self.URL, {'request_ids': self.invitation.request_id})

        mocked.assert_called_with(
            '{0}_{1}'.format(self.invitation.request_id, self.fb_user.uid),
            method='delete'
        )

    def test_accept_invitation_with_next_set(self, _):
        self.assertTrue(self.client.login(facebook_user=self.fb_user))
        url = 'http://www.google.com/'
        self.invitation.next = url
        self.invitation.save()

        res = self.client.get(self.URL, {
            'request_ids': self.invitation.request_id
        })
        self.assertTemplateUsed('js-redirect-to.html')
        self.assertEqual(res.context['redirect_to'], url)

    def test_accept_invitation_when_not_authed(self, _):
        '''An unauthed user should get redirected for authing while
        keeping the request_ids in the next attribute.
        '''
        res = self.client.get(self.URL, {
            'request_ids': self.invitation.request_id
        })

        self.assertEqual(res.status_code, 302)
        self.assertTrue('request_ids' in res.get('Location'))
        self.assertTrue(str(self.invitation.request_id) in res.get('Location'))


@patch('requests.get', return_value=FakeResponse(200))
class Rescraping(TestCase):
    """Not much to test with this one, but a start for expected behavior
    right now"""
    def test_should_raise_assertion_error_when_not_absolute_url(self, _):
        self.assertRaises(ValueError, rescrape_url, 'fake-url')

    def test_should_return_true_when_all_went_okay(self, _):
        self.assertTrue(rescrape_url('http://something-else.sg/'))

    def test_should_raise_scrapingerror_when_response_other_than_ok(self, _):
        url = 'http://something-else.sg/'
        json = {'something': 'fluffy'}

        with patch('requests.get', return_value=FakeResponse(404, json)):
            try:
                rescrape_url(url)
            except ScrapingError as exc:
                self.assertIn(url, exc.msg)
                self.assertEqual(exc.json, json)
            else:
                self.fail("Should've raised ScrapingError")

    def test_task_successfull(self, _):
        """Do nothing when all is a-ok"""
        tasks.rescrape_urls(['http://something-test/'])

    def test_task_unsuccessfull_invalid_url(self, _):
        url = 'invalid-url'
        with LogCapture() as l:
            tasks.rescrape_urls([url,])

            l.check(
                ('friendface', 'ERROR',
                 'Failed to tell Facebook to rescrape URL "{0}"'.format(url))
            )

    def test_task_unsuccessfull_facebook_response_other_than_ok(self, _):
        url = 'http://something-else.sg/'
        json = {'something': 'fluffy'}

        with patch('requests.get', return_value=FakeResponse(404, json)):
            with LogCapture() as l:
                tasks.rescrape_urls([url,])

                l.check(
                    ('friendface', 'ERROR',
                     'Failed to tell Facebook to rescrape URL '
                     '"{0}"'.format(url)),
                )
                self.assertEqual(l.records[0].facebook_response, json)
