#!/usr/bin/env python

import sys

from setuptools.command.test import test as TestCommand
from setuptools import setup


class PyTest(TestCommand):

  def finalize_options(self):
    TestCommand.finalize_options(self)
    self.test_args = ['-vs', 'ranja']
    self.test_suite = True

  def run_tests(self):
    import pytest
    errno = pytest.main(self.test_args)
    self.handle_exit()
    sys.exit(errno)

  @staticmethod
  def handle_exit():
    import atexit
    atexit._run_exitfuncs()

setup(name='ranja',
    version='0.1',
    description='',
    url='http://github.com/r7ar7a/ranja',
    maintainer='Andras Radnai',
    maintainer_email='r7ar7a@gmail.com',
    keywords='ranja',
    packages=['ranja'],
    install_requires=['Jinja2', 'pyyaml'],
    dependency_links=[],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    zip_safe=False)
