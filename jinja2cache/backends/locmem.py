"""
Thread-safe in-memory cache backend, stolen from Django 1.3.
"""

import time
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.core.cache.backends.base import BaseCache
from django.utils.encoding import smart_str
from django.utils.synch import RWLock

# Global in-memory store of cache data. Keyed by name, to provide
# multiple named local memory caches.
_caches = {}
_expire_info = {}
_locks = {}

def default_key_func(key, key_prefix, version):
    """Default function to generate keys.

    Constructs the key used by all other methods. By default it prepends
    the `key_prefix'. CACHE_KEY_FUNCTION can be used to specify an alternate
    function with custom key making behavior.
    """
    return ':'.join([key_prefix, str(version), smart_str(key)])

class LocMemCache(BaseCache):
    def __init__(self, name, params, key_prefix='', version=1, key_func=None):
        BaseCache.__init__(self, params)
        global _caches, _expire_info, _locks
        self._cache = _caches.setdefault(name, {})
        self._expire_info = _expire_info.setdefault(name, {})
        self._lock = _locks.setdefault(name, RWLock())
        max_entries = params.get('max_entries', 300)
        try:
            self._max_entries = int(max_entries)
        except (ValueError, TypeError):
            self._max_entries = 300
        
        self._cull_frequency = params.get('cull_frequency', None)
        if self._cull_frequency is None:
            try:
                self._cull_frequency = int(max_entries)
            except (ValueError, TypeError):
                self._cull_frequency = 3
        self.key_prefix = smart_str(key_prefix)
        self.version = version
        self.key_func = key_func or default_key_func

    def add(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None or exp <= time.time():
                try:
                    self._set(key, pickle.dumps(value), timeout)
                    return True
                except pickle.PickleError:
                    pass
            return False
        finally:
            self._lock.writer_leaves()

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.reader_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None:
                return default
            elif exp > time.time():
                try:
                    return pickle.loads(self._cache[key])
                except pickle.PickleError:
                    return default
        finally:
            self._lock.reader_leaves()
        self._lock.writer_enters()
        try:
            try:
                del self._cache[key]
                del self._expire_info[key]
            except KeyError:
                pass
            return default
        finally:
            self._lock.writer_leaves()

    def _set(self, key, value, timeout=None):
        if len(self._cache) >= self._max_entries:
            self._cull()
        if timeout is None:
            timeout = self.default_timeout
        self._cache[key] = value
        self._expire_info[key] = time.time() + timeout

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        # Python 2.4 doesn't allow combined try-except-finally blocks.
        try:
            try:
                self._set(key, pickle.dumps(value), timeout)
            except pickle.PickleError:
                pass
        finally:
            self._lock.writer_leaves()

    def has_key(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.reader_enters()
        try:
            exp = self._expire_info.get(key)
            if exp is None:
                return False
            elif exp > time.time():
                return True
        finally:
            self._lock.reader_leaves()

        self._lock.writer_enters()
        try:
            try:
                del self._cache[key]
                del self._expire_info[key]
            except KeyError:
                pass
            return False
        finally:
            self._lock.writer_leaves()

    def _cull(self):
        if self._cull_frequency == 0:
            self.clear()
        else:
            doomed = [k for (i, k) in enumerate(self._cache) if i % self._cull_frequency == 0]
            for k in doomed:
                self._delete(k)

    def _delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            pass
        try:
            del self._expire_info[key]
        except KeyError:
            pass

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        self._lock.writer_enters()
        try:
            self._delete(key)
        finally:
            self._lock.writer_leaves()

    def clear(self):
        self._cache.clear()
        self._expire_info.clear()
    
    def make_key(self, key, version=None):
        """Constructs the key used by all other methods. By default it
        uses the key_func to generate a key (which, by default,
        prepends the `key_prefix' and 'version'). An different key
        function can be provided at the time of cache construction;
        alternatively, you can subclass the cache backend to provide
        custom key making behavior.
        """
        if version is None:
            version = self.version

        new_key = self.key_func(key, self.key_prefix, version)
        return new_key

# For backwards compatibility
class CacheClass(LocMemCache):
    pass
