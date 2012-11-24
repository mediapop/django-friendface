import os
from django.conf import settings
from django.http import HttpRequest
from django.test.testcases import TestCase
from friendface.models import FacebookApplication

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


class FacebookApplicationMatchingTestCase(TestCase):
    fixtures = ["application.json"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.path = '/foo'
        self.request.META = {'SERVER_NAME': 'www.foo.com', 'SERVER_PORT': 80}

    def test_get_for_request_matches_canvas_url(self):
        os.environ["HTTPS"] = "off"
        app_url = 'http://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}
        FacebookApplication.objects.update(canvas_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_canvas_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}

        FacebookApplication.objects.update(secure_canvas_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_page_tab_url(self):
        os.environ["HTTPS"] = "off"
        app_url = 'http://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}
        FacebookApplication.objects.update(page_tab_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_secure_page_tab_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'
        self.request.POST = {'signed_request': 'asdf'}

        FacebookApplication.objects.update(secure_page_tab_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_website_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'

        FacebookApplication.objects.update(website_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)

    def test_get_for_request_matches_mobile_url(self):
        os.environ["HTTPS"] = "on"
        app_url = 'https://www.foo.com/'

        FacebookApplication.objects.update(mobile_web_url = app_url)
        application = FacebookApplication.get_for_request(self.request)
        self.assertIsInstance(application, FacebookApplication)


    def test_get_for_request_raises_exception_on_no_match(self):
        with self.assertRaises(FacebookApplication.DoesNotExist):
            FacebookApplication.get_for_request(self.request)