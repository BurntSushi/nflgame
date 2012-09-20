from distutils.core import setup
import os

longdesc = \
'''An API to retrieve and read NFL Game Center JSON data. It can work with real-time data, which can be used for fantasy football.

nflgame works by parsing the same JSON data that powers NFL.com's live GameCenter. Therefore, nflgame can be used to report game statistics while a game is being played.

The package comes pre-loaded with game data from every pre- and regular season game from 2009 up until August 28, 2012. Querying such data does not actually ping NFL.com.

However, if you try to search for data in a game that is being currently played, the JSON data will be downloaded from NFL.com at each request (so be careful not to inspect for data too many times while a game is being played). If you ask for data for a particular game that hasn't been cached to disk but is no longer being played, it will be automatically cached to disk so that no further downloads are required.'''

try:
    docfiles = map(lambda s: 'doc/%s' % s, list(os.walk('doc'))[0][2])
except IndexError:
    docfiles = []

setup(
    name='nflgame',
    author='Andrew Gallant',
    author_email='andrew@burntsushi.net',
    version='1.1.5',
    license='WTFPL',
    description='An API to retrieve and read NFL Game Center JSON data. '
                'It can work with real-time data, which can be used for '
                'fantasy football.',
    long_description=longdesc,
    url='https://github.com/BurntSushi/nflgame',
    classifiers=[
        'License :: Public Domain',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Home Automation',
    ],
    platforms='ANY',
    packages=['nflgame'],
    package_dir={'nflgame': 'nflgame'},
    package_data={'nflgame': ['players.json', 'gamecenter-json/*.json.gz']},
    data_files=[('share/doc/nflgame', ['README', 'CHANGELOG', 'COPYING',
                                       'INSTALL']),
                ('share/doc/nflgame/doc', docfiles)],
    scripts=[]
)
