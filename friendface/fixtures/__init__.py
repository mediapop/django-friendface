from django.contrib.auth.models import User
import random

import factory
from mock import Mock

from friendface.models import (FacebookUser, FacebookApplication,
                               FacebookPage, PageAdmin)


def random_hex_string(length, max_length=None):
    str_length = max_length or length
    length = length / 2
    if max_length: max_length = max_length / 2

    return ('{:0%dx}' % str_length).format(random.randrange(
        str_length ** random.randrange(length, max_length)),
    )


def create_user(connect_user_with_app=False):
    fb_app = FacebookApplicationFactory.build()
    fb_app._pre_save = Mock(return_value=True)
    fb_app.save()

    fb_user = FacebookUserFactory.build()
    if connect_user_with_app: fb_user.application = fb_app
    fb_user.save()

    user = User.objects.create_user(username=random_hex_string(15),
                                    email=fb_user.email)
    user.first_name = fb_user.first_name
    user.last_name = fb_user.last_name
    user.set_unusable_password()
    user.save()

    profile = user.get_profile()
    profile.facebook = fb_user
    profile.save()

    return (fb_user, user)


class FacebookUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FacebookUser

    uid = 50021084
    first_name = 'Random user'
    last_name = factory.Sequence(lambda n: 'No. {}'.format(n))
    access_token = factory.LazyAttribute(lambda a: random_hex_string(50, 64))
    application_id = 1234567890
    email = factory.Sequence(lambda n: 'fake-user-{}'.format(n))


class FacebookApplicationFactory(factory.DjangoModelFactory):
        FACTORY_FOR = FacebookApplication

        id = 1234567890
        name = 'Test application for the greater good'
        secret = 'b0809lcjkf095'
        default_scope = 'user_likes,email'
        namespace = 'fake-test-app'
        website_url = 'http://testserver/dashboard/'


class FacebookPageFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FacebookPage

    id = 123456


class PageAdminFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PageAdmin

    user = factory.SubFactory(FacebookUserFactory)
    page = factory.SubFactory(FacebookPageFactory)
