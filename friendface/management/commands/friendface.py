from importlib import import_module
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...tasks import rescrape_urls

logger = logging.getLogger('friendface')


class Command(BaseCommand):
    args = '<subcommand> [arguments, ...]'
    help = 'Available subcommands: rescrape <app> [<app>, ...]'
    valid_subcommands = ['rescrape']

    def handle(self, *args, **options):
        if not args or args[0] not in self.valid_subcommands:
            raise CommandError('Not a valid subcommand. '
                               'Valids ones are: {0}'.format(
                                   ', '.join(self.valid_subcommands)
                                ))
        else:
            getattr(self, args[0])(*args[1:])


    def rescrape(self, *args):
        """Will load {app}.facebook_urls and then rescrape all the URLs in the
        iteratable `urls`. The URLs in the list need to all be
        absolute and contain a domain name, otherwise Facebook will
        not recognize them.

        Example:
          website/facebook_urls.py
            urls = ('https://apps.facebook.com/namespaced/',)

        This command internally calls `tasks.rescrape_urls` that takes
        a list of URLs and then scrapes them one-by-one. If Celery is
        installed then it'll handed of as a task to Celery otherwise
        it'll be run instantly.
        """
        for app in args:
            if  app not in settings.INSTALLED_APPS:
                raise CommandError('{0} not in INSTALLED_APPS'.format(app))

            try:
                module = import_module('{0}.facebook_urls'.format(app))
            except ImportError:
                raise CommandError(
                    'No facebook_urls module for app {0}'.format(app)
                )

            self.stdout.write('Rescraping urls for: {0}'.format(app))

            no_urls = 20
            for i in xrange(0, len(module.urls), no_urls):
                urls = module.urls[i:i+no_urls]
                logger.debug('rescraping urls: %s', urls)

                rescrape_urls.delay(urls)
