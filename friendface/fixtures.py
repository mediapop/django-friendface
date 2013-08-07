from django.contrib.auth.models import User
import random

import factory
from mock import Mock

from .models import (FacebookApplication, FacebookInvitation, FacebookUser,
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
                application_kwargs=None,
                facebook_user_kwargs=None):
    if not application_kwargs:
        application_kwargs = {}
    if not facebook_user_kwargs:
        facebook_user_kwargs = {}
    if not application:
        application = FacebookApplicationFactory.create(**application_kwargs)

    fb_user = FacebookUserFactory.build(**facebook_user_kwargs)
    if connect_user_with_app: fb_user.application = application
    fb_user.save()

    user = UserFactory.create(email=fb_user.email,
                              first_name=fb_user.first_name,
                              last_name=fb_user.last_name)

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

        id = factory.Sequence(lambda n: (8 ** random.randrange(16, 20)) + n)
        name = factory.Sequence(lambda n: 'Application {0}'.format(n))
        secret = factory.LazyAttribute(lambda x: random_hex_string(16, 32))
        default_scope = 'user_likes,email'
        namespace = 'fake-test-app'
        website_url = 'http://testserver/'

        @classmethod
        def _prepare(cls, create, **kwargs):
            if('website_url' in kwargs
               and not kwargs['website_url'].startswith('http')):
                kwargs['website_url'] = 'http://testserver{0}'.format(
                    kwargs['website_url']
                )

            return (super(FacebookApplicationFactory, cls)
                    ._prepare(create, **kwargs))


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(
        lambda n: '{0}-{1}'.format(n, random_hex_string(20))
    )
    email = factory.Sequence(
        lambda n: 'user-account-{0}@example.com'.format(n)
    )

    @classmethod
    def _prepare(cls, create, **kwargs):
        user = super(UserFactory, cls)._prepare(False, **kwargs)
        user.set_unusable_password()

        if create:
            user.save()

        return user


class FacebookUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FacebookUser

    uid = factory.Sequence(lambda n: (8 ** random.randrange(16, 20)) + n)
    first_name = 'Random user'
    last_name = factory.Sequence(lambda n: 'No. {}'.format(n))
    access_token = factory.LazyAttribute(lambda a: random_hex_string(50, 64))
    application = factory.SubFactory(FacebookApplicationFactory)
    email = factory.Sequence(lambda n: 'fake-user-{}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):
        user = super(FacebookUserFactory, cls)._prepare(False, **kwargs)
        user.send_notification = Mock(return_value=True)

        if create:
            user.save()

        return user


class FacebookPageFactory(DontRunPreSaveMixin, factory.DjangoModelFactory):
    FACTORY_FOR = FacebookPage
    id = 1


class PageAdminFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PageAdmin

    user = factory.SubFactory(FacebookUserFactory)
    page = factory.SubFactory(FacebookPageFactory)


class FacebookInvitationFactory(DontRunPreSaveMixin,
                                factory.DjangoModelFactory):
    FACTORY_FOR = FacebookInvitation

    request_id = factory.Sequence(lambda n: 8 ** random.randrange(16, 20) + n)
    application = factory.SubFactory(FacebookApplicationFactory)
    sender = factory.SubFactory(
        FacebookUserFactory,
        application=factory.SelfAttribute('..application')
    )
    receiver = factory.SubFactory(
        FacebookUserFactory,
        application=factory.SelfAttribute('..application')
    )
