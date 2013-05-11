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

# Extra URLs to cover all views when testing.
if 'test' in sys.argv:
    urlpatterns += patterns('friendface.views',
        url('^install/$', FacebookApplicationInstallRedirectView.as_view(), name='friendface.views.install'),
    )