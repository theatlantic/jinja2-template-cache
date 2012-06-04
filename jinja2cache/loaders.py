import os
import warnings
import hashlib

try:
    import cPickle as pickle
except ImportError:
    import pickle

from jinja2 import loaders
from jinja2.utils import open_if_exists
from jinja2.exceptions import TemplateNotFound

from .settings import JINJA2_CACHE_MSTAT_DISABLED

template_search_caches = {}


def hash_search_path(search_path):
    md5 = hashlib.md5()
    md5.update(pickle.dumps(set(search_path)))
    return md5.hexdigest()


class MemFirstBaseLoader(loaders.BaseLoader):

    def load(self, environment, name, globals=None):
        """Loads a template.  This method looks up the template in the cache
        or loads one by calling :meth:`get_source`.  Subclasses should not
        override this method as loaders working on collections of other
        loaders (such as :class:`PrefixLoader` or :class:`ChoiceLoader`)
        will not call this method but `get_source` directly.
        """
        code = None
        if globals is None:
            globals = {}

        # first we try to get the source for this template together
        # with the filename and the uptodate function.
        filename, uptodate = self.get_source(environment, name)

        # try to load the code from the bytecode cache if there is a
        # bytecode cache configured.
        bcc = environment.bytecode_cache
        if bcc is not None:
            bucket = bcc.get_bucket(environment, name, filename, '')
            code = bucket.code

        # if we don't have code so far (not cached, no longer up to
        # date) etc. we compile the template
        if code is None:
            source = self._get_filename_contents(filename)
            code = environment.compile(source, name, filename)
            # if the bytecode cache is available and the bucket doesn't
            # have a code so far, we give the bucket the new code and put
            # it back to the bytecode cache.
            if bcc is not None and bucket.code is None:
                bucket.code = code
                bcc.set_bucket(bucket)

        return environment.template_class.from_code(environment, code,
                                                    globals, uptodate)

    def _get_filename_contents(self, filename):
        f = open_if_exists(filename)
        if f is not None:
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()
            return contents
        else:
            raise Exception("template file %s not found" % (filename))


class MemFirstFileLoader(MemFirstBaseLoader, loaders.FileSystemLoader):

    template_search_cache = {}

    def __init__(self, searchpath, encoding='utf-8'):
        super(MemFirstFileLoader, self).__init__(searchpath, encoding)
        searchpath_id = hash_search_path(searchpath)
        if searchpath_id not in template_search_caches:
            template_search_caches[searchpath_id] = {}
        self.template_search_cache = template_search_caches[searchpath_id]

    def _get_uptodatefunc(self, filename):
        mtime = os.path.getmtime(filename)
        def uptodate():
            try:
                return os.path.getmtime(filename) == mtime
            except OSError:
                return False
        return uptodate

    def get_source(self, environment, template):
        # uptodate is a callable that returns True if a file has not been
        # modified.
        #
        # If JINJA2_CACHE_MSTAT_DISABLED is True, uptodate always returns True.
        # Setting JINJA2_CACHE_MSTAT_DISABLED to True also causes template file
        # search results to be cached.
        uptodate = lambda: True

        if JINJA2_CACHE_MSTAT_DISABLED:
            if template in self.template_search_cache:
                return self.template_search_cache[template], uptodate

        pieces = loaders.split_template_path(template)
        for searchpath in self.searchpath:
            filename = os.path.join(searchpath, *pieces)
            f = open_if_exists(filename)
            if f is None:
                continue
            f.close()

            if JINJA2_CACHE_MSTAT_DISABLED:
                self.template_search_cache[template] = filename
            else:
                uptodate = self._get_uptodatefunc(filename)

            return filename, uptodate

        raise TemplateNotFound(template)


class MemFirstChoiceLoader(MemFirstBaseLoader):

    def __init__(self, loaders, encoding='utf-8'):
        self.loaders = loaders
        self.encoding = encoding

    def get_source(self, environment, template):
        for loader in self.loaders:
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(template)

    def list_templates(self):
        found = set()
        for loader in self.loaders:
            found.update(loader.list_templates())
        return sorted(found)


def get_loaders():
    loaders = []
    from django.conf import settings
    for loader in settings.TEMPLATE_LOADERS:
        if isinstance(loader, basestring):
            loader_obj = jinja_loader_from_django_loader(loader)
            if loader_obj:
                loaders.append(loader_obj)
            else:
                warnings.warn('Cannot translate loader: %s' % loader)
        else: # It's assumed to be a Jinja2 loader instance.
            loaders.append(loader)
    return loaders


def jinja_loader_from_django_loader(django_loader):
    """Attempts to make a conversion from the given Django loader to an
    similarly-behaving Jinja loader.

    :param django_loader: Django loader module string.
    :return: The similarly-behaving Jinja loader, or None if a similar loader
        could not be found.
    """
    for substr, func in _JINJA_LOADER_BY_DJANGO_SUBSTR.iteritems():
        if substr in django_loader:
            return func()
    return None


def _make_jinja_app_loader():
    """Makes an 'app loader' for Jinja which acts like
    :mod:`django.template.loaders.app_directories`.
    """
    from django.template.loaders.app_directories import app_template_dirs
    return MemFirstFileLoader(app_template_dirs)


def _make_jinja_filesystem_loader():
    """Makes a 'filesystem loader' for Jinja which acts like
    :mod:`django.template.loaders.filesystem`.
    """
    from django.conf import settings
    return MemFirstFileLoader(settings.TEMPLATE_DIRS)


# Determine loaders from Django's conf.
_JINJA_LOADER_BY_DJANGO_SUBSTR = { # {substr: callable, ...}
    'app_directories': _make_jinja_app_loader,
    'filesystem': _make_jinja_filesystem_loader,
}
