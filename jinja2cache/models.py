# models is loaded by django from INSTALLED_APPS, include tplcache to
# insert our JINJA2 loaders.
from .tplcache import cache, bccache