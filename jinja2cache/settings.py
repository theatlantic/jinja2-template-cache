from django.conf import settings

JINJA2_CACHE_BACKEND = getattr(settings, 'JINJA2_CACHE_BACKEND', None)
JINJA2_CACHE_ENABLED = getattr(settings, 'JINJA2_CACHE_ENABLED', False)

# Whether to check for updates with an mstat before loading a template from cache.
JINJA2_CACHE_MSTAT_DISABLED = getattr(settings, 'JINJA2_CACHE_MSTAT_DISABLED', True)
