from django.http import HttpResponse
from django.views.generic import View

from friendface.views import FacebookHandleInvitationMixin, \
    FacebookPostAsGetMixin


class FacebookInvitationHandler(FacebookHandleInvitationMixin, View):
    handle_invitation_called = False

    def get(self, request, *args, **kwargs):
        if self.handle_invitation_called:
            return HttpResponse('Handle invitation called')
        else:
            return HttpResponse('Uh-oh no handle invitation not called')

    def handle_invitation(self, invitation):
        self.handle_invitation_called = True


class TestFacebookPostAsGetMixinView(FacebookPostAsGetMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("get")

    def post(self, request, *args, **kwargs):
        return HttpResponse("post")
