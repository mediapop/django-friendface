from django.conf.urls import patterns, include, url

# from test.views import EmojiTestReplaceTagView
from friendface.views import FacebookApplicationInstallRedirectView

urlpatterns = patterns(
    '',
    url(r'facebook/', include('friendface.urls')),
)

urlpatterns += patterns(
    'friendface.views',
    url('^install/$', FacebookApplicationInstallRedirectView.as_view(),
        name='friendface.views.install'),
)
