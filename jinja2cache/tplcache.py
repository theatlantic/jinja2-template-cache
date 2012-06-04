"""
Template Caching framework (just like regular caching, only for templates!)
"""
import collections
import copy

from django.core.cache import get_cache, parse_backend_uri
# jinja2.bccache.MemcachedBytecodeCache also works with redis
from jinja2.bccache import MemcachedBytecodeCache

from .settings import JINJA2_CACHE_BACKEND, JINJA2_CACHE_ENABLED


def is_dict(obj):
    return isinstance(obj, collections.Mapping)


if JINJA2_CACHE_ENABLED and JINJA2_CACHE_BACKEND is None:
    cache = None
    bccache = None
else:
    cache_kwargs = {}
    if is_dict(JINJA2_CACHE_BACKEND) and 'BACKEND' in JINJA2_CACHE_BACKEND:
        cache_kwargs = copy.deepcopy(JINJA2_CACHE_BACKEND)
        cache_backend = cache_kwargs.pop('BACKEND')
        cache = get_cache(cache_backend, **cache_kwargs)
    elif isinstance(JINJA2_CACHE_BACKEND, basestring):
        scheme, host, params = parse_backend_uri(JINJA2_CACHE_BACKEND)
        if scheme == 'locmem':
            from .backends.locmem import LocMemCache
            cache = LocMemCache('templates', {'timeout': None})
            bccache = MemcachedBytecodeCache(cache)
        else:
            cache = get_cache(JINJA2_CACHE_BACKEND)
            if hasattr(cache, '_cache'):
                bccache = MemcachedBytecodeCache(cache._cache)
            else:
                bccache = MemcachedBytecodeCache(cache)


if not JINJA2_CACHE_ENABLED or cache is None:
    cache_loader = None
else:
    from django.conf import settings
    from .loaders import get_loaders, MemFirstChoiceLoader

    cache_loader = MemFirstChoiceLoader(get_loaders())
    if not hasattr(settings, 'JINJA2_ENVIRONMENT_OPTIONS'):
        settings.JINJA2_ENVIRONMENT_OPTIONS = {}

    settings.JINJA2_ENVIRONMENT_OPTIONS.update({
        'loader': cache_loader,
        'bytecode_cache': bccache,
    })
