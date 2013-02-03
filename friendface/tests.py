# -*- encoding: utf-8 -*-
from django.contrib.auth.models import User
from facebook import GraphAPI
import os
from mock import patch
from django.http import HttpRequest
from django.test.testcases import TestCase
from friendface.models import FacebookApplication, FacebookAuthorization, FacebookUser

TEST_USER = {
    'id': 12345678,
    'first_name': 'Kit',
    'last_name': 'Sunde',
    'email': 'foo@foo.com'
}


class FacebookAuthorizedTestCase(TestCase):
    fixtures = ["friendface/application.json"]

    def setUp(self):
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
    fixtures = ["friendface/application.json"]

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


class FacebookApplicationMatchingTestCase(TestCase):
    fixtures = ["friendface/application.json"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.path = '/foo'
        self.request.META = {'SERVER_NAME': 'www.foo.com', 'SERVER_PORT': 80}

    def test_get_for_request_matches_canvas_url(self):
        os.environ["HTTPS"] = "off"
        app_url = 'http://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}
        FacebookApplication.objects.update(canvas_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_canvas_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}

        FacebookApplication.objects.update(secure_canvas_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_page_tab_url(self):
        os.environ["HTTPS"] = "off"
        app_url = 'http://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}
        FacebookApplication.objects.update(page_tab_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_page_tab_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}

        FacebookApplication.objects.update(secure_page_tab_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_website_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'

        FacebookApplication.objects.update(website_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_mobile_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'

        FacebookApplication.objects.update(mobile_web_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_canvas_url_with_no_signed_request(self):
        os.environ["HTTPS"] = "off"
        app_url = 'http://www.foo.com/'
        self.request.POST = {'other_data': 'asdf'}
        FacebookApplication.objects.update(canvas_url=app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_raises_exception_on_no_match(self):
        with self.assertRaises(FacebookApplication.DoesNotExist):
            FacebookApplication.get_for_request(self.request)
