from setuptools import setup

setup(
    name='PyArinst',
    version='1.0',
    description='Python SDK for Arinst devices',
    author='Ilya Danilenko',
    author_email='ilya@eadsoft.com',
    packages=['pyarinst'],
    install_requires=[line.strip() for line in open("requirements.txt").readlines()]
)