from urlparse import urlparse, urljoin
from django import template
from django.templatetags.future import url

register = template.Library()

class FacebookUrlNode(template.Node):
    def __init__(self, url_node):
        self.url_node = url_node

    def render(self, context):
        #@todo We should let the page URL take priority.
        local_path = self.url_node.render(context)
        request = context.get('request')
        if not request: return ''
        if not hasattr(request, 'facebook'): return ''
        application = context['request'].facebook
        canvas_url = urlparse(application.canvas_url)
        clipped_path = local_path.lstrip(canvas_url.path)
        return urljoin(application.canvas_url, clipped_path)


@register.tag
def fburl(parser, token):
    return FacebookUrlNode(url(parser, token))