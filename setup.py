#!/usr/bin/env python
"""
django-friendface
======

Django-friendface is a django application for interacting with Facebook. It's
goal is to completely implement Facebook's API's in a django centric fashion
and to support projects that have multiple Facebook Applications.
"""

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# Hack to prevent stupid "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when running `python
# setup.py test` (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
for m in ('multiprocessing', 'billiard'):
    try:
        __import__(m)
    except ImportError:
        pass


class PyTest(TestCommand):
    def finalize_options(self):
        self.verbose = False
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # nose2 has limited support for setup.py test
        # https://nose2.readthedocs.org/en/latest/differences.html#limited-support-for-python-setup-py-test
        import test.runtests

setup(
    name='django-friendface',
    version='0.2.5',
    author='Kit Sunde',
    author_email='kit@mediapop.co',
    url='http://github.com/mediapop/django-friendface',
    description='Django-friendface is an easy implementation of the Facebook API\'s for Django',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        # This seem to install from a different source, why?
        #'facebook-sdk==0.3.0',
        'requests>=1.0',
        'mock',
        'django-model-utils',
        'factory-boy',
    ],
    dependency_links = [
        #'git+git://github.com/Celc/facebook-sdk.git#egg=facebook-sdk',
    ],
    cmdclass={'test': PyTest},
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