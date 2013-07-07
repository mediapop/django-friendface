# flake8: noqa
import sys

from django.conf.urls import *

from friendface.views import FacebookApplicationInstallRedirectView

urlpatterns = patterns('friendface.views',
    url(r'^application/(?P<application_id>\d+)/authorize/', 'authorize', name="authorize"),
    url(r'^authorization/(?P<authorization_id>\d+)/authorized/$', 'authorized', name="authorized"),
    url(r'^record-invitation/$', 'record_facebook_invitation', name="record_facebook_invitation"),
    url(r'^channel/$', 'channel', name="channel"),
    url(r'^install/(?P<application_id>\d+)/$', FacebookApplicationInstallRedirectView.as_view(), name='friendface.views.install'),
)

# Extra URLs to coverall views when testing.  This is ugly and should
# dissapear, question is how to make sure normal django projects
# doesn't run our test cases.
if 'test' in sys.argv:
    from django.http import HttpResponse
    from django.views.generic import View
    from .views import FacebookHandleInvitationMixin

    class FacebookInvitationHandler(FacebookHandleInvitationMixin, View):
        handle_invitation_called = False

        def get(self, request, *args, **kwargs):
            if self.handle_invitation_called:
                return HttpResponse('Handle invitation called')
            else:
                return HttpResponse('Uh-oh no handle invitation not called')

        def handle_invitation(self, invitation):
            self.handle_invitation_called = True


    urlpatterns += patterns(
        'friendface.views',
        url('^install/$', FacebookApplicationInstallRedirectView.as_view(),
            name='friendface.views.install'),
        url('^invitation-handler/$', FacebookInvitationHandler.as_view(),
            name='friendface.views.invitation_handler'),
    )