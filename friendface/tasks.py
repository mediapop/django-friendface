import logging

logger = logging.getLogger('friendface')

try:
    from celery import task
except ImportError:
    # To replicate the behavior of celery as close as possible so we
    # can still prepare as tasks even if celery isn't actually
    # installed or used.
    def task(*args, **kwargs):
        class Inner(object):
            def __init__(self, func):
                self.func = func

            def __call__(self, *a, **kwa):
                return self.func(*a, **kwa)

            def __getattr__(self, name):
                return self.func

        return Inner

from friendface.shortcuts import rescrape_url, ScrapingError


@task()
def rescrape_urls(urls):
    """Will in turn call shortcuts.rescrape_url on each URL in `urls`."""
    for url in iter(urls):
        try:
            rescrape_url(url)
        except (ScrapingError, ValueError) as e:
            extra_logging = {}
            if hasattr(e, 'json'):
                extra_logging['facebook_response'] = e.json

            logger.error(
                'Failed to tell Facebook to rescrape URL "%s"',
                url,
                extra=extra_logging
            )