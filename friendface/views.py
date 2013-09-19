import json
import random
import urllib2

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.baseconv import BASE62_ALPHABET
from facebook import GraphAPI
from django.views.generic import RedirectView, TemplateView, View

from friendface.models import (FacebookApplication, FacebookAuthorization,
                               FacebookUser, FacebookInvitation)
from friendface.shortcuts import redirectjs

# Match Facebook user agents for places where special logic is needed.
FACEBOOK_USER_AGENT = 'facebookexternalhit'


def set_mobile(request):
    request.session['is_facebook_mobile'] = True


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
    facebook_user_data = {
        'access_token': access_token,
        'first_name': request_data['first_name'],
        'last_name': request_data['last_name'],
        'locale': request_data.get('locale'),
        'timezone': request_data.get('timezone'),
        'religion': request_data.get('religion'),
        'location': request_data.get('location', {}).get('name'),
        'gender': request_data.get('gender'),
        'email': request_data.get('email')
    }
    facebook_user, created = FacebookUser.objects.get_or_create(
        uid=request_data['id'],
        application=auth.application,
        defaults=facebook_user_data)
    if created:
        username = "".join(random.choice(BASE62_ALPHABET) for i in xrange(30))
        user = User.objects.create_user(username=username,
                                        email=facebook_user.email)
        user.first_name = facebook_user.first_name[0:30]
        user.last_name = facebook_user.last_name[0:30]
        user.set_unusable_password()
        facebook_user.user = user
        user.save()
        facebook_user.save()
    else:
        facebook_user.__dict__.update(facebook_user_data)
        facebook_user.save()

    authenticated_user = authenticate(facebook_user=facebook_user)

    if authenticated_user is not None:
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
    response = render(request, 'channel.html')
    response['Cache-Control'] = 'public, max-age=31536000'  # One year

    return response


def record_facebook_invitation(request):
    """Expects a post request formatted just as the Facebook App
    request response sent through the wire encoded by jQuery.

    If you need to do processing after the invitation has been created
    then use FacebookInvitationCreateView.

    POST keys:
      request: The Facebook request id
      to[]: A list of Facebook UIDs that the request was sent to.
      next: Optional argument for where the user is to be redirected after
            the invitation has been accepted.

    Returns:
      400 when no request has been set
      201 when invitations has been successfully created
    """
    request_id = request.POST.get('request')
    if not request_id:
        return HttpResponseBadRequest('No request set.')
    try:
        request.facebook.user
    except FacebookUser.DoesNotExist:
        HttpResponse(json.dumps({'result': 'error',
                                 'error': 'no friendface user'}),
                     content_type='application/json',
                     status=403)

    for recipient in request.POST.getlist('to[]'):
        FacebookInvitation.create_with_receiver(
            receiver=recipient,
            request_id=request_id,
            application=request.facebook.application,
            sender=request.facebook.user,
            next=request.POST.get('next', ''))

    return HttpResponse(json.dumps({'result': 'ok'}),
                        content_type='application/json',
                        status=201)


class FacebookPostAsGetMixin(object):
    """ Treat facebook requests with a decoded signed_request as GET. """
    def dispatch(self, request, *args, **kwargs):
        # Mobile seems to keep being dropped, so add in a little extra when
        # redirecting and hope that it sticks
        mobile = request.GET.get('mobile')
        if mobile and mobile.lower() == 'true':
            request.session['is_facebook_mobile'] = True

        if request.FACEBOOK:
            if not hasattr(self, 'get'):
                raise ImproperlyConfigured("FacebookPostAsGetMixin needs a "
                                           "get method to dispatch to")
            setattr(self, 'post', self.get)

        return super(FacebookPostAsGetMixin, self).dispatch(
            request, *args, **kwargs)


class MobileView(RedirectView):
    """If you set Facebooks mobile view to go here all fburl's will
    behave like regular url.

    To use install it in your urls.py as:

        url(r'^mobile/', MobileView.as_view(), name='mobile')

    It automatically replaces the string 'mobile/' with '' and then
    redirects the user to that page.
    """
    redirect_url = None
    permanent = False
    mobile_prefix = 'mobile/'
    replacement_string = ''

    def get_mobile_prefix(self):
        return self.mobile_prefix

    def get_replacement_string(self):
        return self.replacement_string

    def get_redirect_url(self):
        if self.redirect_url:
            url = self.redirect_url
        else:
            url = self.request.path.replace(self.get_mobile_prefix(),
                                            self.get_replacement_string())

        return '{0}{1}mobile=true'.format(
            url,
            '&' if '?' in url else '?'
        )

    def dispatch(self, request, *args, **kwargs):
        set_mobile(request)
        return super(MobileView, self).dispatch(request, *args, **kwargs)


class FacebookEnabledTemplateView(FacebookPostAsGetMixin, TemplateView):
    """ So that we can use TemplateView in urls.py even when on Facebook. """


class FacebookAppAuthMixin(object):
    """ This will cause authentication that will go back to the canvas (if on
    facebook) or the page (request.FACEBOOK is not present)"""
    # This is the URL that authentication should redirec to after user
    # has authed successfully
    auth_url = ''

    def get_auth_url(self):
        if self.auth_url:
            return self.auth_url

        session = getattr(self.request, 'session', {})

        if self.request.FACEBOOK and not session.get('is_facebook_mobile'):
            return self.request.facebook.build_canvas_url(
                self.request.get_full_path()
            )
        else:
            return self.request.build_absolute_uri()

    def redirect(self, url):
        #@todo This could work like authorize() and cause 1 less redirect.
        return redirect(url)

    def dispatch(self, request, *args, **kwargs):
        if getattr(request, 'mobile', False):
            set_mobile(request)

        self.request = request

        if request.user.is_authenticated() and request.facebook:
            try:
                # @todo In Django 1.5 it should be possible to reduce this to:
                # request.user.facebook.application == request.facebook
                facebook_user = request.user.get_profile().facebook
                if(not facebook_user
                   or request.facebook != facebook_user.application):
                    raise ObjectDoesNotExist  # @todo Pick a better exception?
            except ObjectDoesNotExist:
                pass
            else:
                return super(FacebookAppAuthMixin, self).dispatch(
                    request, *args, **kwargs
                )
        # If it's the scraper then don't require it to authorize, just
        # continue on and let it see the page (and read the sharing message)
        elif request.META.get('HTTP_USER_AGENT',
                              '').startswith(FACEBOOK_USER_AGENT):
            return super(FacebookAppAuthMixin, self).dispatch(
                request, *args, **kwargs
            )

        auth_url = self.get_auth_url()
        return self.redirect(request.facebook.get_authorize_url(auth_url))


class FacebookApplicationInstallRedirectView(RedirectView):
    """Redirect to the correct place where the user can install this
    app to their Facebook page.

    To use simply add the following to your urls.py
      url('^install/$', FacebookAppInstallRedirectView.as_view(),
          name='install')

    Accepted kwargs:
      application_id: If application_id is captured in urls.py that will
                      be used instead of the automatic from friendface.

    Configurable variables:
      app_redirect_field: The field on FacebookApplication that will be
                          used for return URL after the app has installed.
                          Default: 'secure_canvas_url'
    """
    app_redirect_field = 'secure_canvas_url'
    permanent = False

    def dispatch(self, request, *args, **kwargs):
        if 'application_id' in kwargs:
            try:
                self.application = FacebookApplication.objects.get(
                    pk=kwargs.pop('application_id')
                )
            except FacebookApplication.DoesNotExist:
                return HttpResponseBadRequest('No application with that id.')
        else:
            if hasattr(request, 'facebook'):
                self.application = request.facebook
            else:
                return HttpResponseBadRequest('No app configured on this URL.')

        return (super(FacebookApplicationInstallRedirectView, self)
                .dispatch(request, *args, **kwargs))

    def get_redirect_url(self, **kwargs):
        if not self.app_redirect_field:
            raise ImproperlyConfigured(
                'FacebookApplicationInstallRedirectView requires '
                'app_redirect_field to be set'
            )

        return ('https://www.facebook.com/dialog/pagetab'
                '?app_id={0}&redirect_uri={1}').format(
                    self.application.pk,
                    getattr(self.application, self.app_redirect_field)
                )


class FacebookInvitationMixin(object):
    """Handle Facebook Invitations directed towards the root canvas
    URL. This mixin should be used together with `FacebookAppAuthMixin`
    to handle unauthed users who accept a request.

    Look at `FacebookHandleInvitationMixin` for that.
    """
    # @todo Deleting the invitation objects could be pushed to celery.
    # @todo It can currently only delete similar invitation objects. If a user
    # has multiple invitation leading to different places, it would need to be
    # dealt with individually.

    def handle_invitation(self, invitation):
        """To be able to add custom logic after an invitation has been
        accepted. An invitation object sent in for further logic.
        """
        pass

    def dispatch(self, request, *args, **kwargs):
        request_ids = request.GET.get('request_ids')

        if not request_ids:
            return super(FacebookInvitationMixin, self).dispatch(
                request, *args, **kwargs
            )

        # If the user is not authenticated just return and let
        # FacebookAppAuthMixin deal with getting us an authed user.
        if(not request.user.is_authenticated()
           or not request.user.get_profile().facebook):
            return super(FacebookInvitationMixin, self).dispatch(
                request, *args, **kwargs
            )

        facebook_user = request.user.get_profile().facebook
        next_url = None
        for request_id in request_ids.split(','):
            try:
                invitation = FacebookInvitation.objects.get(
                    request_id=request_id,
                    receiver=facebook_user,
                    accepted=None
                )
                invitation.accepted = timezone.now()
                invitation.save()

                if invitation.next:
                    next_url = invitation.next
            except FacebookInvitation.DoesNotExist:
                pass
            else:
                self.handle_invitation(invitation)

        if next_url:
            return redirectjs(next_url)

        return super(FacebookInvitationMixin, self).dispatch(
            request, *args, **kwargs
        )


class FacebookHandleInvitationMixin(FacebookInvitationMixin,
                                    FacebookAppAuthMixin):
    """Users accepting invitations and authing them if they're not
    authed before the invitations get accepted.
    """


class FacebookInvitationCreateView(View):
    """ Use this view if you need to do some extra handling after the
    invitation has been created by overriding `handle_invitation`.

    If only stock behavior is needed look at `record_facebook_invitation`.
    """

    def handle_invitation(self, invitation):
        """Called after the invitation has been created in get_context_data"""
        pass

    def get_context_data(self, **kwargs):
        """
        Expects a post request formatted just as the Facebook App
        request response sent through the wire encoded by jQuery.

        POST keys:
          request: The Facebook request id
          to[]: A list of Facebook UIDs that the request was sent to.
          next: Optional argument for where the user is to be redirected after
                the invitation has been accepted.

        Raises:
           ValueError when request is not available
        """
        context = {}
        request = self.request.POST.get('request')
        if not request: raise ValueError('No request id specified')
        fb_user = self.request.user.get_profile().facebook

        context.update({
            'request_id': request,
            'sender': fb_user,
            'application': self.request.facebook,
            'next': self.request.POST.get('next', ''),
            'invitations': []
        })

        for recipient in self.request.POST.getlist('to[]'):
            invitation = FacebookInvitation.create_with_receiver(
                receiver=recipient,
                request_id=context['request_id'],
                application=context['application'],
                sender=context['sender'],
                next=context['next'],
            )

            context['invitations'].append(invitation)
            self.handle_invitation(invitation)

        return context

    def post(self, *args, **kwargs):
        try:
            self.get_context_data(**kwargs)
        except ValueError as e:
            return HttpResponseBadRequest('No request set. {0}'.format(e))

        return HttpResponse('{"status": "ok"}',
                            content_type='application/json',
                            status=201)


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
                'LikeGateMixin requires get_fan_gate_template to be set '
            )
        return self.like_gate_template

    def get_like_gate_target(self):
        return self.like_gate_target

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        page = request.FACEBOOK.get('page', {})
        like_gate_target = self.get_like_gate_target()
        if(page and not page['liked']
           and (not like_gate_target or int(page['id']) == like_gate_target)):
            return render(request,
                          self.get_like_gate_template(),
                          self.get_context_data(**kwargs))
        elif like_gate_target and int(page.get('id', 0)) != like_gate_target:
            try:  # @todo Drop get_profile() for 1.5
                facebook_user = request.user.get_profile().facebook
                if facebook_user is None: raise ObjectDoesNotExist
            except ObjectDoesNotExist:
                raise ImproperlyConfigured("LikeGate with target must come "
                                           "after facebook auth.")
            if not facebook_user.has_liked(self.get_like_gate_target()):
                return render(request,
                              self.get_like_gate_template(),
                              self.get_context_data(**kwargs))

        return super(LikeGateMixin, self).dispatch(request, *args, **kwargs)
