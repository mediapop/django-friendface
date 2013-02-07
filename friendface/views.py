import json
import random
import urllib2
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ImproperlyConfigured, ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.baseconv import BASE62_ALPHABET
from facebook import GraphAPI
from django.views.generic import TemplateView
from friendface.shortcuts import redirectjs
from friendface.models import (FacebookApplication, FacebookAuthorization,
                               FacebookUser, FacebookInvitation)


def authorized(request, authorization_id):
    auth = FacebookAuthorization.objects.get(id=authorization_id)
    if request.GET.get('error'):
        # @todo Handle user not wanting to auth.
        return redirect(auth.get_absolute_url())

    # @todo We are probably better of using some kind of
    # application_installation custom signal that creates the user.
    code = request.GET.get('code')
    try:
        access_token = auth.get_access_token(code)[0]
    except urllib2.HTTPError:
        return redirect(auth.get_facebook_authorize_url())

    request_data = GraphAPI(access_token).get_object('me')
    facebook_user, created = FacebookUser.objects.get_or_create(
        uid=request_data['id'],
        application=auth.application)
    facebook_user.access_token = access_token
    facebook_user.first_name = request_data['first_name']
    facebook_user.last_name = request_data['last_name']
    facebook_user.locale = request_data.get('locale')
    facebook_user.timezone = request_data.get('timezone')
    facebook_user.religion = request_data.get('religion')
    facebook_user.location = request_data.get('location', {}).get('name')
    facebook_user.gender = request_data.get('gender')
    facebook_user.email = request_data.get('email')
    facebook_user.save()

    authenticated_user = authenticate(facebook_user=facebook_user)
    if authenticated_user is None:
        # @todo import the profile and check if it has a foreignkey to
        # FacebookUser
        username = "".join(random.choice(BASE62_ALPHABET) for i in xrange(30))
        user = User.objects.create_user(username=username)
        user.first_name = facebook_user.first_name
        user.last_name = facebook_user.last_name
        user.email = facebook_user.email
        user.set_unusable_password()

        try:
            profile = user.get_profile()
            profile.facebook = facebook_user
            profile.save()
            authenticated_user = authenticate(facebook_user=facebook_user)
        except SiteProfileNotAvailable:
            user.delete()

    if not authenticated_user is None:
        if authenticated_user.is_active:
            login(request, authenticated_user)
            #@todo handle user not active.
        #@todo what should happen if the user doesn't get logged in?

    return redirectjs(auth.next)


def authorize(request, application_id):
    # 1. ?next=url
    # 2. HTTP_REFERER
    # 3. Application link. (website if canvas is not setup)
    app = FacebookApplication.objects.get(id=application_id)
    next = request.META.get('HTTP_REFERER', app.link)
    next = request.GET.get('next', next)
    scope = request.GET.get("perms", app.default_scope)
    assert(not next is None)
    auth = FacebookAuthorization.objects.create(next=next,
                                                application=app,
                                                scope=scope)
    # Catch 22 problem :(
    auth.redirect_uri = request.build_absolute_uri(auth.get_authorized_url())
    auth.save()

    return redirectjs(auth.get_facebook_authorize_url())


def channel(request):
    return render(request, 'channel.html')


def record_facebook_invitation(request):
    profile = request.user.get_profile()
    application = profile.facebook.application

    request_id = request.POST.get('request')

    for recipient in request.POST.getlist('to[]'):
        FacebookInvitation.create_with_receiver(
            receiver=recipient,
            request_id=request_id,
            application=application,
            sender=profile.facebook
        )

    return HttpResponse(json.dumps({'result': 'ok'}))


class FacebookPostAsGetMixin(object):
    """ Treat facebook requests with a decoded signed_request as GET. """
    def post(self, request, *args, **kwargs):
        if request.FACEBOOK:
            return self.get(request, *args, **kwargs)
        else:
            return self.post(request, *args, **kwargs)

class FacebookEnabledTemplateView(FacebookPostAsGetMixin, TemplateView):
    """ So that we can use TemplateView in urls.py even when on Facebook. """


class FacebookAppAuthMixin(object):
    auth_url = ''

    def auth_redirect_back(self):
        '''
        Define the URL the request should be redirected to after the app has
        been authorized here.
        '''
        raise ValueError('An URL to redirect to after app auth expected.')

    def _generate_auth_url(self):
        next = self.auth_redirect_back()
        self.auth_url = self.request.facebook.get_authorize_url(next)

    def redirect(self, url):
        return redirect(url)

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        self._generate_auth_url()
        if not request.user.is_authenticated():
            return self.redirect(self.auth_url)
        ## With changes to friendface these lines shouldn't be needed since
        ## the middleware handles logout before it goes this far.
        else:
            fb_user = request.user.get_profile().facebook
            if not fb_user or fb_user.application != request.facebook:
                return self.redirect(self.auth_url)

        return super(FacebookAppAuthMixin, self).dispatch(request, *args,
                                                          **kwargs)

class LikeGateMixin(object):
    # @todo If we have concept of a canonical page, that could be the default
    # @todo If we have permissions escalation we could request user_likes on
    # failing to detect a like.
    # @todo Should cache likes.
    # @todo Allow for multiple targets.
    like_gate_template = None
    like_gate_target = None

    def get_like_gate_template(self):
        if not self.like_gate_template:
            raise ImproperlyConfigured(
                "LikeGateMixin requires get_fan_gate_template to return a "
                "template by being overridden or having like_gate_template set")
        return self.like_gate_template

    def dispatch(self, request, *args, **kwargs):
        page = request.FACEBOOK.get('page', {})
        if page and not page['liked'] and (not self.like_gate_target or
                     int(page['id']) == self.like_gate_target):
            return render(request, self.get_like_gate_template())
        elif self.like_gate_target and \
             int(page.get('id', 0)) != self.like_gate_target:
            try: #@todo Drop get_profile() for 1.5
                facebook_user = request.user.get_profile().facebook
                if facebook_user is None: raise ObjectDoesNotExist
            except ObjectDoesNotExist:
                raise ImproperlyConfigured("LikeGate with target must come "
                                           "after facebook auth.")
            if not facebook_user.has_liked(self.like_gate_target):
                return render(request, self.get_like_gate_template())

        return super(LikeGateMixin, self).dispatch(request, *args, **kwargs)