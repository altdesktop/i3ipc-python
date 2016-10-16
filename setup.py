from setuptools import setup
from os import path
from io import open

readme_path = path.join(path.abspath(path.dirname(__file__)), 'README.rst')
long_description = open(readme_path, encoding='utf-8').read()

install_requires = ['enum-compat']

setup(
    name='i3ipc',
    version='1.3.0',
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
    packages=['i3ipc'],
    install_requires=install_requires,
)
