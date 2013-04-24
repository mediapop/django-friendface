# flake8: noqa
from django.conf.urls import *

urlpatterns = patterns('friendface.views',
    url(r'^application/(?P<application_id>\d+)/authorize/', 'authorize', name="authorize"),
    url(r'^authorization/(?P<authorization_id>\d+)/authorized/$', 'authorized', name="authorized"),
    url(r'^record-invitation/$', 'record_facebook_invitation', name="record_facebook_invitation"),
    url(r'^channel/$', 'channel', name="channel"),
)
