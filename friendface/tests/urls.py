from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import TestFacebookPostAsGetMixinView, FacebookAuthView

from views import FacebookInvitationHandler
from friendface.views import FacebookApplicationInstallRedirectView, MobileView

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'facebook/', include('friendface.urls')),

    url('^install/$', FacebookApplicationInstallRedirectView.as_view(),
        name='friendface.views.install'),
    url('^invitation-handler/$', FacebookInvitationHandler.as_view(),
        name='friendface.views.invitation_handler'),
    url('^postasgetmixin/$', TestFacebookPostAsGetMixinView.as_view(),
        name='facebook_post_as_get_mixin'),
    url('^auth-view$', FacebookAuthView.as_view(), name='auth_view'),
    url('^mobile/auth-view$', MobileView.as_view(), name='mobile_view'),
)
