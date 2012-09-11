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
from better_facebook.models import (FacebookApplication, FacebookAuthorization,
                                    FacebookUser, FacebookInvitation)

def authorized(request, authorization_id):
    auth = FacebookAuthorization.objects.get(id = authorization_id)
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
        application = auth.application)
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

    user = authenticate(facebook_user=facebook_user)
    if user is None:
        # @todo import the profile and check if it has a foreignkey to
        # FacebookUser
        username = "".join(random.choice(BASE62_ALPHABET) for i in xrange(30))
        user = User.objects.create_user(username=username)
        user.first_name=facebook_user.first_name
        user.last_name=facebook_user.last_name
        user.email=facebook_user.email
        user.set_unusable_password()

        try:
            profile = user.get_profile()
            profile.facebook = facebook_user
            profile.save()
            user = authenticate(facebook_user=facebook_user)
        except SiteProfileNotAvailable:
            user.delete()

    if not user is None:
        if user.is_active:
            login(request, user)
            #@todo handle user not active.
        #@todo what should happen if the user doesn't get logged in?

    redirect_to = auth.next

    return render(request, 'js-redirect-to.html', locals())


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
                                                application = app,
                                                scope=scope)
    # Catch 22 problem :(
    auth.redirect_uri = request.build_absolute_uri(auth.get_authorized_url())
    auth.save()

    redirect_to = auth.get_facebook_authorize_url()

    return render(request, 'js-redirect-to.html', locals())


def channel(request):
    return render(request, 'channel.html')

def record_facebook_invitation(request):
    profile = request.user.get_profile()
    application = profile.facebook.application

    request_id = request.POST.get('request')

    for recipient in request.POST.getlist('to[]'):
        user, created = FacebookUser.objects.get_or_create(
            uid=recipient,
            application=profile.facebook.application)

        FacebookInvitation.objects.create(
            request_id=request_id,
            application=application,
            sender=profile.facebook,
            receiver=user
        )
    return HttpResponse(json.dumps({'result': 'ok'}))