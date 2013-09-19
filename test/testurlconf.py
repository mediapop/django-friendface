from django.conf.urls import patterns, include, url

from test.views import FacebookInvitationHandler, \
    TestFacebookPostAsGetMixinView
from friendface.views import FacebookApplicationInstallRedirectView

urlpatterns = patterns(
    '',
    url(r'facebook/', include('friendface.urls')),
)

urlpatterns += patterns(
    'friendface.views',
    url('^install/$', FacebookApplicationInstallRedirectView.as_view(),
        name='friendface.views.install'),
    url('^invitation-handler/$', FacebookInvitationHandler.as_view(),
        name='friendface.views.invitation_handler'),
    url('^postasgetmixin/$', TestFacebookPostAsGetMixinView.as_view(),
        name='facebook_post_as_get_mixin'),
)
