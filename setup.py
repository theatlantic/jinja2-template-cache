#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='jinja2-template-cache',
    version='1.0',
    description="A bytecode cache for jinja2 using django cache backends",
    author='Frankie Dintino',
    author_email='fdintino@theatlantic.com',
    url='https://github.com/theatlantic/jinja2-template-cache',
    packages=find_packages(),
    #install_requires=['coffin', 'django>=1.2'],
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'License :: OSI Approved :: BSD License',
    ],
    include_package_data=True,
    zip_safe=False,
)
