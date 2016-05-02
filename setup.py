"""
To install FlyingCircus from source, a cloned repository or an archive, use
``python setup.py install``.

Use ``python setup.py bdist_wheel`` to make distribute as a wheel.bdist_wheel.
"""

# try to use setuptools if available, otherwise fall back on distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from flying_circus import __version__, __author__, __email__, __url__
import os

README = 'README.rst'
try:
    with open(os.path.join(os.path.dirname(__file__), README), 'r') as readme:
        README = readme.read()
except IOError:
    pass

setup(name='FlyingCircus',
      version=__version__,
      description='FlyingCircus Modeling Framework',
      long_description=README,
      author=__author__,
      author_email=__email__,
      url=__url__,
      packages=['flying_circus', 'flying_circus.core'],
      requires=[
          'numpy (>=1.8.2)', 'pint (>=0.7.2)', 'xlrd (>=0.9.4)', 'scipy',
          'dateutil', 'numexpr', 'sphinx'
      ],
      scripts=['flying_circus-quickstart.py'],
      package_data={'flying_circus': [
          'docs/conf.py', 'docs/*.rst', 'docs/Makefile', 'docs/make.bat'
      ]})
