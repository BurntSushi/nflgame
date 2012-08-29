import os
import os.path
import sys

from distutils import sysconfig
from distutils.core import setup

setup(
    name = 'nflgame',
    author = 'Andrew Gallant',
    author_email = 'andrew@burntsushi.net',
    version = '1.0.0',
    license = 'WTFPL',
    description = 'An API to retrieve and read NFL Game Center JSON data.',
    long_description = 'See README',
    url = 'https://github.com/BurntSushi/nflgame',
    platforms = 'ANY',
    packages = ['nflgame'],
    package_dir = {'nflgame': '.'},
    package_data = {'nflgame': ['gamecenter-json/*.json']},
    data_files = [('share/doc/pytyle3', ['README', 'COPYING', 'INSTALL'])],
    scripts = []
)

