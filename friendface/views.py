import json
import random
import urllib2
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
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
    """ This will cause authentication that will go back to the canvas (if on
    facebook) or the page (request.FACEBOOK is not present)"""
    auth_url = ''

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            try:
                # @todo In Django 1.5 it should be possible to reduce this to:
                # request.user.facebook.application == request.facebook
                facebook_user = request.user.get_profile().facebook
                if request.facebook != facebook_user.application:
                    raise ObjectDoesNotExist # @todo Pick a better exception?

                return super(FacebookAppAuthMixin, self).dispatch(request,
                                                                  *args,
                                                                  **kwargs)
            except ObjectDoesNotExist:
                pass
        if not self.auth_url:
            if request.FACEBOOK:
                self.auth_url = request.facebook.build_canvas_url(request.path)
            else:
                self.auth_url = request.build_absolute_url()
        return redirect(request.facebook.get_authorize_url(self.auth_url))

