import logging
from django.http import HttpResponse
from django.template.loader import render_to_string
import requests


logger = logging.getLogger('friendface')


class ScrapingError(Exception):
    def __init__(self, msg, json):
        self.msg = msg
        self.json = json


def redirectjs(redirect_to):
    """Javascript redirect as regular redirects don't affect the top frame."""
    return HttpResponse(render_to_string('js-redirect-to.html', locals()))


def rescrape_url(url):
    """Tell Facebook to re-scrape an URL so they don't show stale content

    Returns:
      bool: If Facebook returned 200 OK response
    """
    if not url.startswith('http'):
        raise ValueError('url needs to be absolute. (http://..)')

    logger.debug('Scraping %s', url)
    res = requests.post('http://graph.facebook.com/', params={
        'id': url,
        'scrape': 'true',
    })
    logger.debug("Facebook replied %s", res)

    if res.status_code == requests.codes.ok:
        return True
    else:
        raise ScrapingError('Problem rescraping {0}'.format(url),
                            res.json())
