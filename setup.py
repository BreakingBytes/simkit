"""
To install Circus from source, a cloned repository or an archive, use
``python setup.py install``.

Use ``python setup.py bdist_wheel`` to make distribute as a wheel.bdist_wheel.
"""

# try to use setuptools if available, otherwise fall back on distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from circus import __version__, __name__, __author__, __email__, __url__
import os

README = 'README.md'
try:
    with open(os.path.join(os.path.dirname(__file__), README), 'r') as readme:
        README = readme.read()
except IOError:
    pass

setup(name=__name__,
      version=__version__,
      description='Circus Modeling Framework',
      long_description=README,
      author=__author__,
      author_email=__email__,
      url=__url__,
      packages=['circus', 'circus.core'],
      requires=['numpy (>=1.8)', 'quantities (>=0.10)', 'xlrd (>=0.9)'],
      scripts=['circus-quickstart.py'],
      package_data={'circus': [
          'docs/conf.py', 'docs/*.rst', 'docs/Makefile', 'docs/make.bat'
      ]})
