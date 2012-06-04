from django.core.management.base import BaseCommand, CommandError
from jinja2cache.tplcache import cache


class Command(BaseCommand):
    help = 'Flushes all entries from the jinja2 template cache'

    def handle(self, *args, **options):
        if cache is None:
            raise CommandError("Jinja2 template cache is not enabled or no "
                               "backend is defined\n")
        try:
            cache.clear()
        except Exception, e:
            raise CommandError(u"Failed to flush jinja2 template cache: %e\n" % e)

        self.stdout.write("Successfully flushed jinja2 template cache\n")
