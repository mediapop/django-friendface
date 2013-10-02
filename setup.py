#!/usr/bin/env python
"""
django-friendface
======

Django-friendface is a django application for interacting with Facebook. It's
goal is to completely implement Facebook's API's in a django centric fashion
and to support projects that have multiple Facebook Applications.
"""

from setuptools import setup, find_packages

install_requires = [
    'facebook-sdk',
    'requests>=1.0.0',
    'pytz',
    'django-model-utils',
    'django>=1.4,<1.5',
]

tests_requires = [
    'mock',
    'django>=1.4,<1.5',
    'django-discover-runner',
    'factory-boy',
    'coverage',
    'testfixtures',
    'flake8',
]


setup(
    name='django-friendface',
    version='0.2.5',
    author='Kit Sunde',
    author_email='kit@mediapop.co',
    url='http://github.com/mediapop/django-friendface',
    description='Django-friendface is an easy implementation of the '
                'Facebook API\'s for Django',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={'tests': tests_requires},
    dependency_links=[
        'https://github.com/Celc/facebook-sdk/tarball/master#egg=facebook-sdk',
    ],
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
