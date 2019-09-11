#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os

from setuptools import setup, find_packages

REQUIRES_PYTHON = '>=3.4.0'
REQUIRED = ['python-xlib']
EXTRAS = {}

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, 'i3ipc', '__version__.py')) as f:
    exec(f.read(), about)


setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=long_description,
    author=about['__author__'],
    author_email=about['__author_email__'],
    python_requires=REQUIRES_PYTHON,
    url=about['__url__'],
    packages=find_packages(exclude=['test', '*.test', '*.test.*', 'test.*']),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='BSD',
    keywords='i3 i3wm extensions add-ons',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
