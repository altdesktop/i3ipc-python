#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'i3ipc'
DESCRIPTION = 'An improved Python library for i3wm extensions'
URL = 'https://github.com/acrisci/i3ipc-python'
EMAIL = 'tony@dubstepdish.com'
AUTHOR = 'Tony Crisci'
REQUIRES_PYTHON = '>=3.4.0'
VERSION = '1.7.1'

REQUIRED = ['enum-compat', 'python-xlib']
EXTRAS = {}

here = os.path.abspath(os.path.dirname(__file__))

try:
    with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace('-', '_').replace(' ', '_')
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
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
