from django.core.urlresolvers import reverse
from django.test import TestCase

from friendface.fixtures import create_user


class TemplateTagsTest(TestCase):
    def setUp(self):
        create_user(application_kwargs={
            'canvas_url': 'http://somewhere.sg/'
        })

    def test_should_render_template_tag(self):
        res = self.client.get(reverse('template_tag'))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.content,
            'https://apps.facebook.com/fake-test-app/postasgetmixin/'
        )
