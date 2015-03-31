from setuptools import setup
from os import path
import sys

here = path.abspath(path.dirname(__file__))

long_description = """
i3ipc is a library for creating scripts and extensions to interact with i3. You
can send commands or respond to window manager events.

For more information on the ipc interface:

http://i3wm.org/docs/ipc.html

Examples:

https://github.com/acrisci/i3ipc-python/tree/master/examples
"""

install_requires = []
if sys.version_info >= (3,):
    install_requires.append('python3-xlib')
else:
    install_requires.append('python-xlib')
if sys.version_info <= (3, 3):
    install_requires.append('enum34')

setup(
    name='i3ipc',
    version='1.1.2',
    description='An improved Python library for i3wm extensions',
    long_description=long_description,
    url='https://github.com/acrisci/i3ipc-python',
    author='Tony Crisci',
    author_email='tony@dubstepdish.com',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='i3 i3wm extensions add-ons',
    py_modules=['i3ipc'],
    install_requires=install_requires,
)
