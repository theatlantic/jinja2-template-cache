jinja2-template-cache
=====================

**jinja2-template-cache** is a project that provides a means to use django cache
backends and bytecode caches for [Jinja2](http://jinja.pocoo.org/) templates
rendered with [coffin](https://github.com/coffin/coffin). It was created by
developers at [The Atlantic](http://www.theatlantic.com/).


Installation
------------

The recommended way to install from source is with pip:

```bash
pip install -e git+git://github.com/theatlantic/jinja2-template-cache.git#egg=jinja2-template-cache
```

If the source is already checked out, use setuptools:

```bash
python setup.py install
```


Usage
-----

In order to enable the jinja2 template cache, several changes to settings.py
are required.

**1**) `'jinja2cache'` must be added to `INSTALLED_APPS`. It *must* precede
       `'coffin'` in the list.

```python
INSTALLED_APPS = (
    # ...
    'jinja2cache',
    'coffin',
    # ...
)
```

**2**) `JINJA2_CACHE_ENABLED` must be set to `True`

```python
JINJA2_CACHE_ENABLED = True
```

**3**) `JINJA2_CACHE_BACKEND` must be defined. This can use either the
       pre-django 1.3 URI based version of the backend name, or the newer
       [dictionary-based version](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CACHES).
       If using the dictionary-based version with `LocMemCache` on django,
       1.2 be sure to use the modified `LocMemCache` included with this
       package. The local memory cache is the recommended setting.

```python
JINJA2_CACHE_BACKEND = 'locmem://'

JINJA2_CACHE_BACKEND = {
    'BACKEND': 'jinja2cache.backends.locmem.LocMemCache',
}
```

**4**) Optionally, `JINJA2_CACHE_MSTAT_DISABLED` can be set to `True`, which
       will disable lookups on file modification times before loading from the
       cache. This will also cache the results of django template searches at
       the module level. Depending on the server setup, clearing this cache
       could require a server restart or a wsgi touch, if running in mod_wsgi
       daemon mode.

```python
JINJA2_CACHE_MSTAT_DISABLED = True
```


Django Management Commands
--------------------------

This package provides the management command `jinjacache_flush` to clear the
contents of the `JINJA2_CACHE_BACKEND`.

```bash
python manage.py jinjacache_flush
```


License
-------
jinja2-template-cache is licensed under the
[BSD 2-Clause License](http://www.opensource.org/licenses/bsd-license.php) and
is copyright The Atlantic Media Company. View the `LICENSE` file under the root
directory for complete license and copyright information.
