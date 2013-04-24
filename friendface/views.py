import json
import random
import urllib2
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
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
        user = User.objects.create_user(username=username,
                                        email=facebook_user.email)
        user.first_name = facebook_user.first_name
        user.last_name = facebook_user.last_name
        user.set_unusable_password()
        user.save()

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
            sender=profile.facebook,
            next=request.POST.get('next'))

    return HttpResponse(json.dumps({'result': 'ok'}))


class FacebookPostAsGetMixin(object):
    """ Treat facebook requests with a decoded signed_request as GET. """
    def dispatch(self, request, *args, **kwargs):
        if request.FACEBOOK:
            if not hasattr(self, 'get'):
                raise ImproperlyConfigured("FacebookPostAsGetMixin needs a "
                                           "get method to dispatch to")
            setattr(self, 'post', self.get)

        return super(FacebookPostAsGetMixin, self).dispatch(
            request, *args, **kwargs)


class FacebookEnabledTemplateView(FacebookPostAsGetMixin, TemplateView):
    """ So that we can use TemplateView in urls.py even when on Facebook. """


class FacebookAppAuthMixin(object):
    """ This will cause authentication that will go back to the canvas (if on
    facebook) or the page (request.FACEBOOK is not present)"""
    auth_url = ''

    def get_auth_url(self):
        if self.auth_url:
            return self.auth_url

        if self.request.FACEBOOK:
            return self.request.facebook.build_canvas_url(self.request.path)
        else:
            return self.request.build_absolute_uri()

    def redirect(self, url):
        #@todo This could work like authorize() and cause 1 less redirect.
        return redirect(url)

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if request.user.is_authenticated() and request.facebook:
            try:
                # @todo In Django 1.5 it should be possible to reduce this to:
                # request.user.facebook.application == request.facebook
                facebook_user = request.user.get_profile().facebook
                if(not facebook_user
                   or request.facebook != facebook_user.application):
                    raise ObjectDoesNotExist # @todo Pick a better exception?

                return super(FacebookAppAuthMixin, self).dispatch(request,
                                                                  *args,
                                                                  **kwargs)
            except ObjectDoesNotExist:
                pass

        auth_url = self.get_auth_url()
        return self.redirect(request.facebook.get_authorize_url(auth_url))


class FacebookInvitationMixin(object):
    """ Handle Facebook Invitations directed towards the root canvas URL. """
    # @todo Deleting the invitation objects could be pushed to celery.
    # @todo It can currently only delete similar invitation objects. If a user
    # has multiple invitation leading to different places, it would need to be
    # dealt with individually.

    def dispatch(self, request, *args, **kwargs):
        request_ids = request.GET.get('request_ids')
        if not request_ids:
            return super(FacebookInvitationMixin, self).dispatch(request,
                                                                 *args,
                                                                 **kwargs)

        # Make sure the user is logged in, so we can read facebook invitation
        # details.
        if not request.user.is_authenticated() or \
                not request.user.get_profile().facebook:
            return super(FacebookInvitationMixin, self).dispatch(request,
                                                                 *args,
                                                                 **kwargs)

        facebook_user = request.user.get_profile().facebook

        next_url = None

        for request_id in request_ids.split(','):
            try:
                invitation = FacebookInvitation.objects.get(
                    request_id=request_id,
                    receiver=facebook_user)
                invitation.accepted = timezone.now()
                invitation.save()
                if invitation.next is None or next == invitation.next:
                    next_url = invitation.next
                    request.facebook.request('%s_%s' % (invitation.request_id,
                                                        facebook_user.uid),
                                             method='delete')
            except FacebookInvitation.DoesNotExist:
                pass

        if next_url:
            return redirect(next_url)

        return super(FacebookInvitationMixin, self).dispatch(request,
                                                             *args,
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

    def get_like_gate_target(self):
        return self.like_gate_target

    def dispatch(self, request, *args, **kwargs):
        page = request.FACEBOOK.get('page', {})
        like_gate_target = self.get_like_gate_target()
        if page and not page['liked'] and (not like_gate_target or
                     int(page['id']) == like_gate_target):
            return render(request, self.get_like_gate_template())
        elif like_gate_target and int(page.get('id', 0)) != like_gate_target:
            try: #@todo Drop get_profile() for 1.5
                facebook_user = request.user.get_profile().facebook
                if facebook_user is None: raise ObjectDoesNotExist
            except ObjectDoesNotExist:
                raise ImproperlyConfigured("LikeGate with target must come "
                                           "after facebook auth.")
            if not facebook_user.has_liked(self.get_like_gate_target()):
                return render(request, self.get_like_gate_template())

        return super(LikeGateMixin, self).dispatch(request, *args, **kwargs)