from distutils.core import setup

setup(
    name='mapper',
    version='0.1.0',
    author='Sarah Bird, Florian Pilz & Mihai Dincă',
    author_email='sarah@aptivate.org',
    packages=['ocds_mapper'],
    scripts=[],
    url='https://github.com/dincamihai/mapper',
    license='LICENSE',
    description='Map csv files to open contracting data standard.',
    long_description=open('README.md').read(),
    install_requires=[],
    extras_require={
        'test': ['mock']
    }
)
