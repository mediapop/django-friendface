from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

def redirectjs(redirect_to):
    """Javascript redirect as regular redirects don't affect the top frame."""
    return HttpResponse(render_to_string('js-redirect-to.html', locals()))
