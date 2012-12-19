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
        application = request.facebook
        return application.build_canvas_url(local_path)


@register.tag
def fburl(parser, token):
    return FacebookUrlNode(url(parser, token))
