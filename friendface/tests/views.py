from django.http import HttpResponse
from django.views.generic import View

from friendface.views import FacebookHandleInvitationMixin


class FacebookInvitationHandler(FacebookHandleInvitationMixin, View):
    handle_invitation_called = False

    def get(self, request, *args, **kwargs):
        if self.handle_invitation_called:
            return HttpResponse('Handle invitation called')
        else:
            return HttpResponse('Uh-oh no handle invitation not called')

    def handle_invitation(self, invitation):
        self.handle_invitation_called = True
