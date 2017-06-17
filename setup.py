import os
import sys
from setuptools import setup

# make sure we use qredis from the source
_this_dir = os.path.dirname(__file__)
sys.path.insert(0, _this_dir)

import mice

requirements = [
    'gevent',
]

with open(os.path.join(_this_dir, 'README.rst')) as f:
    readme = f.read()

setup(
    name='microIcePAP',
    version=mice.__version__,
    description="Library to control ESRF IcePAP motor controller",
    long_description=readme,
    author="Tiago Coutinho",
    author_email='coutinhotiago@gmail.com',
    url='https://github.com/tiagocoutinho/microIcePAP',
    packages=['mice'],
    install_requires=requirements,
    zip_safe=False,
    keywords='IcePAP',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
