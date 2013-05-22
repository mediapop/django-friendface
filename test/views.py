from django.http import HttpResponse
from django.views.generic import View

from friendface.views import FacebookHandleInvitationMixin


class FacebookInvitationHandler(FacebookHandleInvitationMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('OK')
