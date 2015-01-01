from __future__ import absolute_import, division, print_function
import argparse
import time
import json
import os
import sys
import urllib2
import xml.dom.minidom as xml

import nflgame
from nflgame import OrderedDict


def year_phase_week(year=None, phase=None, week=None):
    cur_year, _ = nflgame.live.current_year_and_week()
    season_types = (
        ('PRE', xrange(0, 4 + 1)),
        ('REG', xrange(1, 17 + 1)),
        ('POST', xrange(1, 4 + 1)),
    )
    for y in range(2009, cur_year+1):
        if year is not None and year != y:
            continue
        for p, weeks in season_types:
            if phase is not None and phase != p:
                continue
            for w in weeks:
                if week is not None and week != w:
                    continue
                yield y, p, w


def schedule_url(year, stype, week):
    """
    Returns the NFL.com XML schedule URL. `year` should be an
    integer, `stype` should be one of the strings `PRE`, `REG` or
    `POST`, and `gsis_week` should be a value in the range
    `[0, 17]`.
    """
    xmlurl = 'http://www.nfl.com/ajax/scorestrip?'
    if stype == 'POST':
        week += 17
        if week == 21:  # NFL.com you so silly
            week += 1
    return '%sseason=%d&seasonType=%s&week=%d' % (xmlurl, year, stype, week)


def week_schedule(year, stype, week):
    """
    Returns a list of dictionaries with information about each game in
    the week specified. The games are ordered by gsis_id. `year` should
    be an integer, `stype` should be one of the strings `PRE`, `REG` or
    `POST`, and `gsis_week` should be a value in the range `[1, 17]`.
    """
    url = schedule_url(year, stype, week)
    try:
        dom = xml.parse(urllib2.urlopen(url))
    except urllib2.HTTPError:
        print >> sys.stderr, 'Could not load %s' % url
        return []

    games = []
    for g in dom.getElementsByTagName("g"):
        gsis_id = g.getAttribute('eid')
        games.append({
            'eid': gsis_id,
            'wday': g.getAttribute('d'),
            'year': year,
            'month': int(gsis_id[4:6]),
            'day': int(gsis_id[6:8]),
            'time': g.getAttribute('t'),
            'season_type': stype,
            'week': week,
            'home': g.getAttribute('h'),
            'away': g.getAttribute('v'),
            'gamekey': g.getAttribute('gsis'),
        })
    return games


def new_schedule():
    """
    Builds an entire schedule from scratch.
    """
    sched = OrderedDict()
    for year, stype, week in year_phase_week():
        update_week(sched, year, stype, week)
    return sched


def update_week(sched, year, stype, week):
    """
    Updates the schedule for the given week in place. `year` should be
    an integer year, `stype` should be one of the strings `PRE`, `REG`
    or `POST`, and `week` should be an integer in the range `[1, 17]`.
    """
    for game in week_schedule(year, stype, week):
        sched[game['eid']] = game


def write_schedule(fpath, sched):
    alist = []
    for gsis_id in sorted(sched):
        alist.append([gsis_id, sched[gsis_id]])
    json.dump({'time': time.time(), 'games': alist},
              open(fpath, 'w+'), indent=1, sort_keys=True,
              separators=(',', ': '))


def eprint(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def run():
    parser = argparse.ArgumentParser(
        description='Updates nflgame\'s schedule to correspond to the latest '
                    'information.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    aa = parser.add_argument
    aa('--json-update-file', type=str, default=None,
       help='When set, the file provided will be updated in place with new '
            'schedule data from NFL.com. If this option is not set, then the '
            '"schedule.json" file that comes with nflgame will be updated '
            'instead.')
    aa('--rebuild', action='store_true',
       help='When set, the entire schedule will be rebuilt.')
    aa('--year', default=None, type=int,
       help='Force the update to a specific year.')
    aa('--phase', default=None, choices=['PRE', 'REG', 'POST'],
       help='Force the update to a specific phase.')
    aa('--week', default=None, type=int,
       help='Force the update to a specific week.')
    args = parser.parse_args()

    if args.json_update_file is None:
        args.json_update_file = nflgame.sched._sched_json_file

    # Before doing anything laborious, make sure we have write access to
    # the JSON database.
    if not os.access(args.json_update_file, os.W_OK):
        eprint('I do not have write access to "%s".' % args.json_update_file)
        eprint('Without write access, I cannot update the schedule.')
        sys.exit(1)

    if args.rebuild:
        sched = new_schedule()
    else:
        sched, last = nflgame.sched._create_schedule(args.json_update_file)
        print('Last updated: %s' % last)

        if (args.year, args.phase, args.week) == (None, None, None):
            year, week = nflgame.live.current_year_and_week()
            phase = nflgame.live._cur_season_phase
            update_week(sched, year, phase, week)
        else:
            for y, p, w in year_phase_week(args.year, args.phase, args.week):
                print('Updating (%d, %s, %d)...' % (y, p, w))
                update_week(sched, y, p, w)
    write_schedule(args.json_update_file, sched)

if __name__ == '__main__':
    run()
