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


def create_user(connect_user_with_app=False,
                application=None,
                application_kwargs={},
                facebook_user_kwargs={}):
    if not application:
        application = FacebookApplicationFactory.create(**application_kwargs)

    fb_user = FacebookUserFactory.build(**facebook_user_kwargs)
    if connect_user_with_app: fb_user.application = application
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

    return (fb_user, user, application)


class DontRunPreSaveMixin(object):
    @classmethod
    def _prepare(cls, create, **kwargs):
        model = super(DontRunPreSaveMixin, cls)._prepare(False, **kwargs)
        model._pre_save = Mock(return_value=True)

        if create:
            model.save()

        return model


class FacebookApplicationFactory(DontRunPreSaveMixin,
                                 factory.DjangoModelFactory):
        FACTORY_FOR = FacebookApplication

        id = factory.LazyAttribute(lambda _: 8 ** random.randrange(16, 20))
        name = 'Test application for the greater good'
        secret = factory.LazyAttribute(lambda x: random_hex_string(16, 32))
        default_scope = 'user_likes,email'
        namespace = 'fake-test-app'
        website_url = 'http://testserver/dashboard/'

        @classmethod
        def _prepare(cls, create, **kwargs):
            if('website_url' in kwargs
               and not kwargs['website_url'].startswith('http')):
                kwargs['website_url'] = 'http://testserver{0}'.format(
                    kwargs['website_url']
                )

            return (super(FacebookApplicationFactory, cls)
                    ._prepare(create, **kwargs))


class FacebookUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FacebookUser

    uid = factory.LazyAttribute(lambda _: 8 ** random.randrange(16, 20))
    first_name = 'Random user'
    last_name = factory.Sequence(lambda n: 'No. {}'.format(n))
    access_token = factory.LazyAttribute(lambda a: random_hex_string(50, 64))
    application_id = 0  # Fake app unless someone overrides application
    email = factory.Sequence(lambda n: 'fake-user-{}'.format(n))


class FacebookPageFactory(DontRunPreSaveMixin, factory.DjangoModelFactory):
    FACTORY_FOR = FacebookPage

    id = factory.LazyAttribute(lambda _: 8 ** random.randrange(16, 20))


class PageAdminFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PageAdmin

    user = factory.SubFactory(FacebookUserFactory)
    page = factory.SubFactory(FacebookPageFactory)
