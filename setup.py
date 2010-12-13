from distutils.core import setup
from ttag import get_version

setup(
    name='django-ttag',
    version=get_version(),
    description="A template tag constructor library for Django.",
    long_description=open('README.rst').read(),
    author='Chris Beaven',
    author_email='chris@lincolnloop.com',
    license='MIT',
    url='http://github.com/lincolnloop/django-ttag',
    packages=[
        'ttag',
        'ttag.tests',
        'ttag.tests.setup'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
