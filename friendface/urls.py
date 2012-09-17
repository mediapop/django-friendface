from django.conf.urls import *

urlpatterns = patterns('friendface.views',
    (r'^application/(?P<application_id>\d+)/authorize/', 'authorize'),
    (r'^authorization/(?P<authorization_id>\d+)/authorized/$', 'authorized'),
    (r'^record-invitation/$', 'record_facebook_invitation'),
    (r'^channel/$', 'channel'),
)