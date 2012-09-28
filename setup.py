#!/usr/bin/env python
"""
django-friendface
======

Django-friendface is a django application for interacting with Facebook. It's
goal is to completely implement Facebook's API's in a django centric fashion
and to support projects that have multiple Facebook Applications.
"""

from setuptools import setup, find_packages

setup(
    name='django-friendface',
    version='0.2',
    author='Kit Sunde',
    author_email='kit@mediapop.co',
    url='http://github.com/mediapop/django-friendface',
    description='Django-friendface is an easy implementation of the Facebook API\'s for Django',
    long_description=__doc__,
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    install_requires=[
        # This seem to install from a different source, why?
        #'facebook-sdk==0.3.0',
        'requests==0.14.0'
    ],
    dependency_links = [
        #'git+git://github.com/Celc/facebook-sdk.git#egg=facebook-sdk',
    ],
    test_suite='runtests.runtests',
    include_package_data=True,
    entry_points={},
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django'
    ],
)