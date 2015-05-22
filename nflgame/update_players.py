# Here's an outline of how this program works.
# Firstly, we load a dictionary mapping GSIS identifier to a dictionary of
# player meta data. This comes from either the flag `json-update-file` or
# nflgame's "players.json" file. We then build a reverse map from profile
# identifier (included in player meta data) to GSIS identifier.
#
# We then look at all players who have participated in the last week of
# play. Any player in this set that is not in the aforementioned mapping
# has his GSIS identifier and name (e.g., `T.Brady`) added to a list of
# players to update.
#
# (N.B. When the initial mappings are empty, then every player who recorded
# a statistic since 2009 is added to this list.)
#
# For each player in the list to update, we need to obtain the profile
# identifier. This is done by sending a single HEAD request to the
# `gsis_profile` URL. The URL is a redirect to their canonical profile page,
# with which we extract the profile id. We add this mapping to both of the
# mappings discussed previously. (But note that the meta data in the GSIS
# identifier mapping is incomplete.)
#
# We now fetch the roster lists for each of the 32 teams from NFL.com.
# The roster list contains all relevant meta data *except* the GSIS identifier.
# However, since we have a profile identifier for each player (which is
# included in the roster list), we can connect player meta data with a
# particular GSIS identifier. If we happen to see a player on the roster that
# isn't in the mapping from profile identifier to GSIS identifier, then we need
# to do a full GET request on that player's profile to retrieve the GSIS
# identifier. (This occurs when a player has been added to a roster but hasn't
# recorded any statistics. e.g., Rookies, benchwarmers or offensive linemen.)
#
# We overwrite the initial dictionary of player meta data for each player in
# the roster data, including adding new entries for new players. We then save
# the updated mapping from GSIS identifier to player meta data to disk as JSON.
# (The JSON dump is sorted by key so that diffs are meaningful.)
#
# This approach requires a few thousand HEAD requests to NFL.com on the first
# run. But after that, most runs will only require 32 requests for the roster
# list (small potatoes) and perhaps a few HEAD/GET requests if there happens to
# be a new player found.

from __future__ import absolute_import, division, print_function
import argparse
import json
import multiprocessing.pool
import os
import re
import sys
import traceback

import httplib2

from bs4 import BeautifulSoup

import nflgame
import nflgame.live
import nflgame.player

urls = {
    'roster': 'http://www.nfl.com/teams/roster?team=%s',
    'gsis_profile': 'http://www.nfl.com/players/profile?id=%s',
}


def new_http():
    http = httplib2.Http(timeout=10)
    http.follow_redirects = False
    return http


def initial_mappings(conf):
    metas, reverse = {}, {}
    try:
        with open(conf.json_update_file) as fp:
            metas = json.load(fp)
        for gsis_id, meta in metas.items():
            reverse[meta['profile_id']] = gsis_id
    except IOError as e:
        eprint('Could not open "%s": %s' % (conf.json_update_file, e))
    # Delete some keys in every entry. We do this to stay fresh.
    # e.g., any player with "team" set should be actively on a roster.
    for k in metas:
        metas[k].pop('team', None)
        metas[k].pop('status', None)
        metas[k].pop('position', None)
    return metas, reverse


def profile_id_from_url(url):
    if url is None:
        return None
    m = re.search('/([0-9]+)/', url)
    return None if m is None else int(m.group(1))


def profile_url(gsis_id):
    resp, content = new_http().request(urls['gsis_profile'] % gsis_id, 'HEAD')
    if resp['status'] != '301':
        return None
    loc = resp['location']
    if not loc.startswith('http://'):
        loc = 'http://www.nfl.com' + loc
    return loc


def gsis_id(profile_url):
    resp, content = new_http().request(profile_url, 'GET')
    if resp['status'] != '200':
        return None
    m = re.search('GSIS\s+ID:\s+([0-9-]+)', content)
    if m is None:
        return None
    gid = m.group(1).strip()
    if len(gid) != 10:  # Can't be valid...
        return None
    return gid


def roster_soup(team):
    resp, content = new_http().request(urls['roster'] % team, 'GET')
    if resp['status'] != '200':
        return None
    return BeautifulSoup(content)


def try_int(s):
    try:
        return int(s)
    except ValueError:
        return 0


def first_int(s):
    m = re.search('[0-9]+', s)
    if m is None:
        return 0
    return int(m.group(0))


def first_word(s):
    m = re.match('\S+', s)
    if m is None:
        return ''
    return m.group(0)


def height_as_inches(txt):
    # Defaults to 0 if `txt` isn't parseable.
    feet, inches = 0, 0
    pieces = re.findall('[0-9]+', txt)
    if len(pieces) >= 1:
        feet = try_int(pieces[0])
        if len(pieces) >= 2:
            inches = try_int(pieces[1])
    return feet * 12 + inches


def meta_from_soup_row(team, soup_row):
    tds, data = [], []
    for td in soup_row.find_all('td'):
        tds.append(td)
        data.append(td.get_text().strip())
    profile_url = 'http://www.nfl.com%s' % tds[1].a['href']

    name = tds[1].a.get_text().strip()
    if ',' not in name:
        last_name, first_name = name, ''
    else:
        last_name, first_name = map(lambda s: s.strip(), name.split(','))

    return {
        'team': team,
        'profile_id': profile_id_from_url(profile_url),
        'profile_url': profile_url,
        'number': try_int(data[0]),
        'first_name': first_name,
        'last_name': last_name,
        'full_name': '%s %s' % (first_name, last_name),
        'position': data[2],
        'status': data[3],
        'height': height_as_inches(data[4]),
        'weight': first_int(data[5]),
        'birthdate': data[6],
        'years_pro': try_int(data[7]),
        'college': data[8],
    }


def meta_from_profile_html(html):
    if not html:
        return html
    try:
        soup = BeautifulSoup(html)
        pinfo = soup.find(id='player-bio').find(class_='player-info')

        # Get the full name and split it into first and last.
        # Assume that if there are no spaces, then the name is the last name.
        # Otherwise, all words except the last make up the first name.
        # Is that right?
        name = pinfo.find(class_='player-name').get_text().strip()
        name_pieces = name.split(' ')
        if len(name_pieces) == 1:
            first, last = '', name
        else:
            first, last = ' '.join(name_pieces[0:-1]), name_pieces[-1]
        meta = {
            'first_name': first,
            'last_name': last,
            'full_name': name,
        }

        # The position is only in the <title>... Weird.
        title = soup.find('title').get_text()
        m = re.search(',\s+([A-Z]+)', title)
        if m is not None:
            meta['position'] = m.group(1)

        # Look for a whole bunch of fields in the format "Field: Value".
        search = pinfo.get_text()
        fields = {'Height': 'height', 'Weight': 'weight', 'Born': 'birthdate',
                  'College': 'college'}
        for f, key in fields.items():
            m = re.search('%s:\s+([\S ]+)' % f, search)
            if m is not None:
                meta[key] = m.group(1)
                if key == 'height':
                    meta[key] = height_as_inches(meta[key])
                elif key == 'weight':
                    meta[key] = first_int(meta[key])
                elif key == 'birthdate':
                    meta[key] = first_word(meta[key])

        # Experience is a little weirder...
        m = re.search('Experience:\s+([0-9]+)', search)
        if m is not None:
            meta['years_pro'] = int(m.group(1))

        return meta
    except AttributeError:
        return None


def players_from_games(existing, games):
    for g in games:
        if g is None:
            continue
        for d in g.drives:
            for p in d.plays:
                for player in p.players:
                    if player.playerid not in existing:
                        yield player.playerid, player.name


def eprint(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def progress(cur, total):
    ratio = 100 * (float(cur) / float(total))
    eprint('\r%d/%d complete. (%0.2f%%)' % (cur, total, ratio), end='')


def progress_done():
    eprint('\nDone!')


def run():
    parser = argparse.ArgumentParser(
        description='Efficiently download player meta data from NFL.com. Note '
                    'that each invocation of this program guarantees at least '
                    '32 HTTP requests to NFL.com',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    aa = parser.add_argument
    aa('--json-update-file', type=str, default=None,
       help='When set, the file provided will be updated in place with new '
            'meta data from NFL.com. If this option is not set, then the '
            '"players.json" file that comes with nflgame will be updated '
            'instead.')
    aa('--simultaneous-reqs', type=int, default=3,
       help='The number of simultaneous HTTP requests sent to NFL.com at a '
            'time. Set this lower if you are worried about hitting their '
            'servers.')
    aa('--full-scan', action='store_true',
       help='Forces a full scan of nflgame player data since 2009. Typically, '
            'this is only done when starting with a fresh JSON player '
            'database. But it can be useful to re-scan all of the players if '
            'past errors went ignored and data is missing. The advantage of '
            'using this option over starting fresh is that an existing '
            '(gsis_id <-> profile_id) mapping can be used for the majority of '
            'players, instead of querying NFL.com for the mapping all over '
            'again.')
    aa('--no-block', action='store_true',
       help='When set, this program will exit with an error instead of '
            'displaying a prompt to continue. This is useful when calling '
            'this program from another script. The idea here is not to block '
            'indefinitely if something goes wrong and the program wants to '
            'do a fresh update.')
    aa('--phase', default=None, choices=['PRE', 'REG', 'POST'],
       help='Force the update to use the given phase of the season.')
    aa('--year', default=None, type=int,
       help='Force the update to use nflgame players from a specific year.')
    aa('--week', default=None, type=int,
       help='Force the update to use nflgame players from a specific week.')
    args = parser.parse_args()

    if args.json_update_file is None:
        args.json_update_file = nflgame.player._player_json_file
    teams = [team[0] for team in nflgame.teams]
    pool = multiprocessing.pool.ThreadPool(args.simultaneous_reqs)

    # Before doing anything laborious, make sure we have write access to
    # the JSON database.
    if not os.access(args.json_update_file, os.W_OK):
        eprint('I do not have write access to "%s".' % args.json_update_file)
        eprint('Without write access, I cannot update the player database.')
        sys.exit(1)

    # Fetch the initial mapping of players.
    metas, reverse = initial_mappings(args)
    if len(metas) == 0:
        if args.no_block:
            eprint('I want to do a full update, but I have been told to\n'
                   'exit instead of asking if you want to continue.')
            sys.exit(1)

        eprint("nflgame doesn't know about any players.")
        eprint("Updating player data will require several thousand HTTP HEAD "
               "requests to NFL.com.")
        eprint("It is strongly recommended to find the 'players.json' file "
               "that comes with nflgame.")
        eprint("Are you sure you want to continue? [y/n] ", end='')
        answer = raw_input()
        if answer[0].lower() != 'y':
            eprint("Quitting...")
            sys.exit(1)

    # Accumulate errors as we go. Dump them at the end.
    errors = []

    # Now fetch a set of players that aren't in our mapping already.
    # Restrict the search to the current week if we have a non-empty mapping.
    if len(metas) == 0 or args.full_scan:
        eprint('Loading players in games since 2009, this may take a while...')
        players = {}

        # Grab players one game a time to avoid obscene memory requirements.
        for _, schedule in nflgame.sched.games.itervalues():
            # If the game is too far in the future, skip it...
            if nflgame.live._game_datetime(schedule) > nflgame.live._now():
                continue
            g = nflgame.game.Game(schedule['eid'])
            for pid, name in players_from_games(metas, [g]):
                players[pid] = name
        eprint('Done.')
    else:
        year, week = nflgame.live.current_year_and_week()
        phase = nflgame.live._cur_season_phase
        if args.phase is not None:
            phase = args.phase
        if args.year is not None:
            year = args.year
        if args.week is not None:
            week = args.week

        eprint('Loading games for %s %d week %d' % (phase, year, week))
        games = nflgame.games(year, week, kind=phase)
        players = dict(players_from_games(metas, games))

    # Find the profile ID for each new player.
    if len(players) > 0:
        eprint('Finding (profile id -> gsis id) mapping for players...')

        def fetch(t):  # t[0] is the gsis_id and t[1] is the gsis name
            return t[0], t[1], profile_url(t[0])
        for i, t in enumerate(pool.imap(fetch, players.items()), 1):
            gid, name, purl = t
            pid = profile_id_from_url(purl)

            progress(i, len(players))
            if purl is None or pid is None:
                errors.append('Could not get profile URL for (%s, %s)'
                              % (gid, name))
                continue

            assert gid not in metas
            metas[gid] = {'gsis_id': gid, 'gsis_name': name,
                          'profile_url': purl, 'profile_id': pid}
            reverse[pid] = gid
        progress_done()

    # Get the soup for each team roster.
    eprint('Downloading team rosters...')
    roster = []

    def fetch(team):
        return team, roster_soup(team)
    for i, (team, soup) in enumerate(pool.imap(fetch, teams), 1):
        progress(i, len(teams))

        if soup is None:
            errors.append('Could not get roster for team %s' % team)
            continue

        tbodys = soup.find(id='result').find_all('tbody')

        for row in tbodys[len(tbodys)-1].find_all('tr'):
            try:
                roster.append(meta_from_soup_row(team, row))
            except Exception:
                errors.append(
                    'Could not get player info from roster row:\n\n%s\n\n'
                    'Exception:\n\n%s\n\n'
                    % (row, traceback.format_exc()))
    progress_done()

    # Find the gsis identifiers for players that are in the roster but haven't
    # recorded a statistic yet. (i.e., Not in nflgame play data.)
    purls = [r['profile_url']
             for r in roster if r['profile_id'] not in reverse]
    if len(purls) > 0:
        eprint('Fetching GSIS identifiers for players not in nflgame...')

        def fetch(purl):
            return purl, gsis_id(purl)
        for i, (purl, gid) in enumerate(pool.imap(fetch, purls), 1):
            progress(i, len(purls))

            if gid is None:
                errors.append('Could not get GSIS id at %s' % purl)
                continue
            reverse[profile_id_from_url(purl)] = gid
        progress_done()

    # Now merge the data from `rosters` into `metas` by using `reverse` to
    # establish the correspondence.
    for data in roster:
        gsisid = reverse.get(data['profile_id'], None)
        if gsisid is None:
            errors.append('Could not find gsis_id for %s' % data)
            continue
        merged = dict(metas.get(gsisid, {}), **data)
        merged['gsis_id'] = gsisid
        metas[gsisid] = merged

    # Finally, try to scrape meta data for players who aren't on a roster
    # but have recorded a statistic in nflgame.
    gids = [(gid, meta['profile_url'])
            for gid, meta in metas.iteritems()
            if 'full_name' not in meta and 'profile_url' in meta]
    if len(gids):
        eprint('Fetching meta data for players not on a roster...')

        def fetch(t):
            gid, purl = t
            resp, content = new_http().request(purl, 'GET')
            if resp['status'] != '200':
                if resp['status'] == '404':
                    return gid, purl, False
                else:
                    return gid, purl, None
            return gid, purl, content
        for i, (gid, purl, html) in enumerate(pool.imap(fetch, gids), 1):
            progress(i, len(gids))
            more_meta = meta_from_profile_html(html)
            if not more_meta:
                # If more_meta is False, then it was a 404. Not our problem.
                if more_meta is None:
                    errors.append('Could not fetch HTML for %s' % purl)
                continue
            metas[gid] = dict(metas[gid], **more_meta)
        progress_done()

    assert len(metas) > 0, "Have no players to add... ???"
    with open(args.json_update_file, 'w+') as fp:
        json.dump(metas, fp, indent=4, sort_keys=True,
                  separators=(',', ': '))

    if len(errors) > 0:
        eprint('\n')
        eprint('There were some errors during the download. Usually this is a')
        eprint('result of an HTTP request timing out, which means the')
        eprint('resulting "players.json" file is probably missing some data.')
        eprint('An appropriate solution is to re-run the script until there')
        eprint('are no more errors (or when the errors are problems on ')
        eprint('NFL.com side.)')
        eprint('-' * 79)
        eprint(('\n' + ('-' * 79) + '\n').join(errors))

if __name__ == '__main__':
    run()
