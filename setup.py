"""
To install Carousel from source, a cloned repository or an archive, use
``python setup.py install``.

Use ``python setup.py bdist_wheel`` to make distribute as a wheel.bdist_wheel.
"""

# try to use setuptools if available, otherwise fall back on distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from carousel import __version__, __author__, __email__, __url__
import os

README = 'README.rst'
try:
    with open(os.path.join(os.path.dirname(__file__), README), 'r') as readme:
        README = readme.read()
except IOError:
    pass

setup(name='Carousel',
      version=__version__,
      description='Model Simulation Framework',
      long_description=README,
      author=__author__,
      author_email=__email__,
      url=__url__,
      packages=['carousel', 'carousel.core'],
      requires=[
          'numpy', 'xlrd', 'scipy', 'python_dateutil', 'numexpr',
          'pint (>=0.7.2)', 'UncertaintyWrapper (>=0.4.1)', 'sphinx', 'nose',
          'pandas', 'pytz', 'pvlib'
      ],
      license='BSD 3-clause',
      scripts=['carousel-quickstart.py'],
      package_data={'carousel': [
          'docs/conf.py', 'docs/*.rst', 'docs/Makefile', 'docs/make.bat'
      ]})
