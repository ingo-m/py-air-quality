"""
py_air_quality setup.

For development installation:
    pip install -e /path/to/py-air-quality

"""

from setuptools import setup, find_packages

setup(name='py_air_quality',
      version='0.0.1',
      description=('Measure and analyse air particulate concentration.'),
      url='https://github.com/ingo-m/py-air-quality',
      author='Ingo Marquardt',
      packages=find_packages(),
      include_package_data=True,
      )
