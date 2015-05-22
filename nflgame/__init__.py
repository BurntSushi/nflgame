"""
nflgame is an API to retrieve and read NFL Game Center JSON data.
It can work with real-time data, which can be used for fantasy football.

nflgame works by parsing the same JSON data that powers NFL.com's live
GameCenter. Therefore, nflgame can be used to report game statistics while
a game is being played.

The package comes pre-loaded with game data from every pre- and regular
season game from 2009 up until the present (I try to update it every week).
Therefore, querying such data does not actually ping NFL.com.

However, if you try to search for data in a game that is being currently
played, the JSON data will be downloaded from NFL.com at each request (so be
careful not to inspect for data too many times while a game is being played).
If you ask for data for a particular game that hasn't been cached to disk
but is no longer being played, it will be automatically cached to disk
so that no further downloads are required.

Here's a quick teaser to find the top 5 running backs by rushing yards in the
first week of the 2013 season:

    #!python
    import nflgame

    games = nflgame.games(2013, week=1)
    players = nflgame.combine_game_stats(games)
    for p in players.rushing().sort('rushing_yds').limit(5):
        msg = '%s %d carries for %d yards and %d TDs'
        print msg % (p, p.rushing_att, p.rushing_yds, p.rushing_tds)

And the output is:

    L.McCoy 31 carries for 184 yards and 1 TDs
    T.Pryor 13 carries for 112 yards and 0 TDs
    S.Vereen 14 carries for 101 yards and 0 TDs
    A.Peterson 18 carries for 93 yards and 2 TDs
    R.Bush 21 carries for 90 yards and 0 TDs

Or you could find the top 5 passing plays in the same time period:

    #!python
    import nflgame

    games = nflgame.games(2013, week=1)
    plays = nflgame.combine_plays(games)
    for p in plays.sort('passing_yds').limit(5):
        print p

And the output is:

    (DEN, DEN 22, Q4, 3 and 8) (4:42) (Shotgun) P.Manning pass
    short left to D.Thomas for 78 yards, TOUCHDOWN. Penalty on
    BAL-E.Dumervil, Defensive Offside, declined.
    (DET, DET 23, Q3, 3 and 7) (5:58) (Shotgun) M.Stafford pass short
    middle to R.Bush for 77 yards, TOUCHDOWN.
    (NYG, NYG 30, Q2, 1 and 10) (2:01) (No Huddle, Shotgun) E.Manning
    pass deep left to V.Cruz for 70 yards, TOUCHDOWN. Pass complete on
    a fly pattern.
    (NO, NO 24, Q2, 2 and 6) (5:11) (Shotgun) D.Brees pass deep left to
    K.Stills to ATL 9 for 67 yards (R.McClain; R.Alford). Pass 24, YAC
    43
    (NYG, NYG 20, Q1, 1 and 10) (13:04) E.Manning pass short middle
    to H.Nicks pushed ob at DAL 23 for 57 yards (M.Claiborne). Pass
    complete on a slant pattern.

If you aren't a programmer, then the
[tutorial for non programmers](http://goo.gl/y05fVj) is for you.

If you need help, please come visit us at IRC/FreeNode on channel `#nflgame`.
If you've never used IRC before, then you can
[use a web client](http://webchat.freenode.net/?channels=%23nflgame).
(Enter any nickname you like, make sure the channel is `#nflgame`, fill in
the captcha and hit connect.)

Failing IRC, the second fastest way to get help is to
[open a new issue on the
tracker](https://github.com/BurntSushi/nflgame/issues/new).
There are several active contributors to nflgame that watch the issue tracker.
We tend to respond fairly quickly!
"""

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict  # from PyPI
import itertools

import nflgame.game
import nflgame.live
import nflgame.player
import nflgame.sched
import nflgame.seq
from nflgame.version import __version__

assert OrderedDict  # Asserting the import for static analysis.
VERSION = __version__  # Deprecated. Backwards compatibility.

NoPlayers = nflgame.seq.GenPlayerStats(None)
"""
NoPlayers corresponds to the identity element of a Players sequences.

Namely, adding it to any other Players sequence has no effect.
"""

players = nflgame.player._create_players()
"""
A dict of all players and meta information about each player keyed
by GSIS ID. (The identifiers used by NFL.com GameCenter.)
"""

teams = [
    ['ARI', 'Arizona', 'Cardinals', 'Arizona Cardinals'],
    ['ATL', 'Atlanta', 'Falcons', 'Atlanta Falcons'],
    ['BAL', 'Baltimore', 'Ravens', 'Baltimore Ravens'],
    ['BUF', 'Buffalo', 'Bills', 'Buffalo Bills'],
    ['CAR', 'Carolina', 'Panthers', 'Carolina Panthers'],
    ['CHI', 'Chicago', 'Bears', 'Chicago Bears'],
    ['CIN', 'Cincinnati', 'Bengals', 'Cincinnati Bengals'],
    ['CLE', 'Cleveland', 'Browns', 'Cleveland Browns'],
    ['DAL', 'Dallas', 'Cowboys', 'Dallas Cowboys'],
    ['DEN', 'Denver', 'Broncos', 'Denver Broncos'],
    ['DET', 'Detroit', 'Lions', 'Detroit Lions'],
    ['GB', 'Green Bay', 'Packers', 'Green Bay Packers', 'G.B.', 'GNB'],
    ['HOU', 'Houston', 'Texans', 'Houston Texans'],
    ['IND', 'Indianapolis', 'Colts', 'Indianapolis Colts'],
    ['JAC', 'Jacksonville', 'Jaguars', 'Jacksonville Jaguars', 'JAX'],
    ['KC', 'Kansas City', 'Chiefs', 'Kansas City Chiefs', 'K.C.', 'KAN'],
    ['MIA', 'Miami', 'Dolphins', 'Miami Dolphins'],
    ['MIN', 'Minnesota', 'Vikings', 'Minnesota Vikings'],
    ['NE', 'New England', 'Patriots', 'New England Patriots', 'N.E.', 'NWE'],
    ['NO', 'New Orleans', 'Saints', 'New Orleans Saints', 'N.O.', 'NOR'],
    ['NYG', 'Giants', 'New York Giants', 'N.Y.G.'],
    ['NYJ', 'Jets', 'New York Jets', 'N.Y.J.'],
    ['OAK', 'Oakland', 'Raiders', 'Oakland Raiders'],
    ['PHI', 'Philadelphia', 'Eagles', 'Philadelphia Eagles'],
    ['PIT', 'Pittsburgh', 'Steelers', 'Pittsburgh Steelers'],
    ['SD', 'San Diego', 'Chargers', 'San Diego Chargers', 'S.D.', 'SDG'],
    ['SEA', 'Seattle', 'Seahawks', 'Seattle Seahawks'],
    ['SF', 'San Francisco', '49ers', 'San Francisco 49ers', 'S.F.', 'SFO'],
    ['STL', 'St. Louis', 'Rams', 'St. Louis Rams', 'S.T.L.'],
    ['TB', 'Tampa Bay', 'Buccaneers', 'Tampa Bay Buccaneers', 'T.B.', 'TAM'],
    ['TEN', 'Tennessee', 'Titans', 'Tennessee Titans'],
    ['WAS', 'Washington', 'Redskins', 'Washington Redskins', 'WSH'],
]
"""
A list of all teams. Each item is a list of different ways to
describe a team. (i.e., JAC, JAX, Jacksonville, Jaguars, etc.).
The first item in each list is always the standard NFL.com
team abbreviation (two or three letters).
"""


def find(name, team=None):
    """
    Finds a player (or players) with a name matching (case insensitive)
    name and returns them as a list.

    If team is not None, it is used as an additional search constraint.
    """
    hits = []
    for player in players.itervalues():
        if player.name.lower() == name.lower():
            if team is None or team.lower() == player.team.lower():
                hits.append(player)
    return hits


def standard_team(team):
    """
    Returns a standard abbreviation when team corresponds to a team in
    nflgame.teams (case insensitive).  All known variants of a team name are
    searched. If no team is found, None is returned.
    """
    team = team.lower()
    for variants in teams:
        for variant in variants:
            if team == variant.lower():
                return variants[0]
    return None


def games(year, week=None, home=None, away=None, kind='REG', started=False):
    """
    games returns a list of all games matching the given criteria. Each
    game can then be queried for player statistics and information about
    the game itself (score, winner, scoring plays, etc.).

    As a special case, if the home and away teams are set to the same team,
    then all games where that team played are returned.

    The kind parameter specifies whether to fetch preseason, regular season
    or postseason games. Valid values are PRE, REG and POST.

    The week parameter is relative to the value of the kind parameter, and
    may be set to a list of week numbers.
    In the regular season, the week parameter corresponds to the normal
    week numbers 1 through 17. Similarly in the preseason, valid week numbers
    are 1 through 4. In the post season, the week number corresponds to the
    numerical round of the playoffs. So the wild card round is week 1,
    the divisional round is week 2, the conference round is week 3
    and the Super Bowl is week 4.

    The year parameter specifies the season, and not necessarily the actual
    year that a game was played in. For example, a Super Bowl taking place
    in the year 2011 actually belongs to the 2010 season. Also, the year
    parameter may be set to a list of seasons just like the week parameter.

    Note that if a game's JSON data is not cached to disk, it is retrieved
    from the NFL web site. A game's JSON data is *only* cached to disk once
    the game is over, so be careful with the number of times you call this
    while a game is going on. (i.e., don't piss off NFL.com.)

    If started is True, then only games that have already started (or are
    about to start in less than 5 minutes) will be returned. Note that the
    started parameter requires pytz to be installed. This is useful when
    you only want to collect stats from games that have JSON data available
    (as opposed to waiting for a 404 error from NFL.com).
    """
    return list(games_gen(year, week, home, away, kind, started))


def games_gen(year, week=None, home=None, away=None,
              kind='REG', started=False):
    """
    games returns a generator of all games matching the given criteria. Each
    game can then be queried for player statistics and information about
    the game itself (score, winner, scoring plays, etc.).

    As a special case, if the home and away teams are set to the same team,
    then all games where that team played are returned.

    The kind parameter specifies whether to fetch preseason, regular season
    or postseason games. Valid values are PRE, REG and POST.

    The week parameter is relative to the value of the kind parameter, and
    may be set to a list of week numbers.
    In the regular season, the week parameter corresponds to the normal
    week numbers 1 through 17. Similarly in the preseason, valid week numbers
    are 1 through 4. In the post season, the week number corresponds to the
    numerical round of the playoffs. So the wild card round is week 1,
    the divisional round is week 2, the conference round is week 3
    and the Super Bowl is week 4.

    The year parameter specifies the season, and not necessarily the actual
    year that a game was played in. For example, a Super Bowl taking place
    in the year 2011 actually belongs to the 2010 season. Also, the year
    parameter may be set to a list of seasons just like the week parameter.

    Note that if a game's JSON data is not cached to disk, it is retrieved
    from the NFL web site. A game's JSON data is *only* cached to disk once
    the game is over, so be careful with the number of times you call this
    while a game is going on. (i.e., don't piss off NFL.com.)

    If started is True, then only games that have already started (or are
    about to start in less than 5 minutes) will be returned. Note that the
    started parameter requires pytz to be installed. This is useful when
    you only want to collect stats from games that have JSON data available
    (as opposed to waiting for a 404 error from NFL.com).
    """
    infos = _search_schedule(year, week, home, away, kind, started)
    if not infos:
        return None

    def gen():
        for info in infos:
            g = nflgame.game.Game(info['eid'])
            if g is None:
                continue
            yield g
    return gen()


def one(year, week, home, away, kind='REG', started=False):
    """
    one returns a single game matching the given criteria. The
    game can then be queried for player statistics and information about
    the game itself (score, winner, scoring plays, etc.).

    one returns either a single game or no games. If there are multiple games
    matching the given criteria, an assertion is raised.

    The kind parameter specifies whether to fetch preseason, regular season
    or postseason games. Valid values are PRE, REG and POST.

    The week parameter is relative to the value of the kind parameter, and
    may be set to a list of week numbers.
    In the regular season, the week parameter corresponds to the normal
    week numbers 1 through 17. Similarly in the preseason, valid week numbers
    are 1 through 4. In the post season, the week number corresponds to the
    numerical round of the playoffs. So the wild card round is week 1,
    the divisional round is week 2, the conference round is week 3
    and the Super Bowl is week 4.

    The year parameter specifies the season, and not necessarily the actual
    year that a game was played in. For example, a Super Bowl taking place
    in the year 2011 actually belongs to the 2010 season. Also, the year
    parameter may be set to a list of seasons just like the week parameter.

    Note that if a game's JSON data is not cached to disk, it is retrieved
    from the NFL web site. A game's JSON data is *only* cached to disk once
    the game is over, so be careful with the number of times you call this
    while a game is going on. (i.e., don't piss off NFL.com.)

    If started is True, then only games that have already started (or are
    about to start in less than 5 minutes) will be returned. Note that the
    started parameter requires pytz to be installed. This is useful when
    you only want to collect stats from games that have JSON data available
    (as opposed to waiting for a 404 error from NFL.com).
    """
    infos = _search_schedule(year, week, home, away, kind, started)
    if not infos:
        return None
    assert len(infos) == 1, 'More than one game matches the given criteria.'
    return nflgame.game.Game(infos[0]['eid'])


def combine(games, plays=False):
    """
    DEPRECATED. Please use one of nflgame.combine_{game,play,max}_stats
    instead.

    Combines a list of games into one big player sequence containing game
    level statistics.

    This can be used, for example, to get PlayerStat objects corresponding to
    statistics across an entire week, some number of weeks or an entire season.

    If the plays parameter is True, then statistics will be dervied from
    play by play data. This mechanism is slower but will contain more detailed
    statistics like receiver targets, yards after the catch, punt and field
    goal blocks, etc.
    """
    if plays:
        return combine_play_stats(games)
    else:
        return combine_game_stats(games)


def combine_game_stats(games):
    """
    Combines a list of games into one big player sequence containing game
    level statistics.

    This can be used, for example, to get GamePlayerStats objects corresponding
    to statistics across an entire week, some number of weeks or an entire
    season.
    """
    return reduce(lambda ps1, ps2: ps1 + ps2,
                  [g.players for g in games if g is not None])


def combine_play_stats(games):
    """
    Combines a list of games into one big player sequence containing play
    level statistics.

    This can be used, for example, to get PlayPlayerStats objects corresponding
    to statistics across an entire week, some number of weeks or an entire
    season.

    This function should be used in lieu of combine_game_stats when more
    detailed statistics such as receiver targets, yards after the catch and
    punt/FG blocks are needed.

    N.B. Since this combines *all* play data, this function may take a while
    to complete depending on the number of games passed in.
    """
    return reduce(lambda p1, p2: p1 + p2,
                  [g.drives.players() for g in games if g is not None])


def combine_max_stats(games):
    """
    Combines a list of games into one big player sequence containing maximum
    statistics based on game and play level statistics.

    This can be used, for example, to get GamePlayerStats objects corresponding
    to statistics across an entire week, some number of weeks or an entire
    season.

    This function should be used in lieu of combine_game_stats or
    combine_play_stats when the best possible accuracy is desired.
    """
    return reduce(lambda a, b: a + b,
                  [g.max_player_stats() for g in games if g is not None])


def combine_plays(games):
    """
    Combines a list of games into one big play generator that can be searched
    as if it were a single game.
    """
    chain = itertools.chain(*[g.drives.plays() for g in games])
    return nflgame.seq.GenPlays(chain)


def _search_schedule(year, week=None, home=None, away=None, kind='REG',
                     started=False):
    """
    Searches the schedule to find the game identifiers matching the criteria
    given.

    The kind parameter specifies whether to fetch preseason, regular season
    or postseason games. Valid values are PRE, REG and POST.

    The week parameter is relative to the value of the kind parameter, and
    may be set to a list of week numbers.
    In the regular season, the week parameter corresponds to the normal
    week numbers 1 through 17. Similarly in the preseason, valid week numbers
    are 1 through 4. In the post season, the week number corresponds to the
    numerical round of the playoffs. So the wild card round is week 1,
    the divisional round is week 2, the conference round is week 3
    and the Super Bowl is week 4.

    The year parameter specifies the season, and not necessarily the actual
    year that a game was played in. For example, a Super Bowl taking place
    in the year 2011 actually belongs to the 2010 season. Also, the year
    parameter may be set to a list of seasons just like the week parameter.

    If started is True, then only games that have already started (or are
    about to start in less than 5 minutes) will be returned. Note that the
    started parameter requires pytz to be installed. This is useful when
    you only want to collect stats from games that have JSON data available
    (as opposed to waiting for a 404 error from NFL.com).
    """
    infos = []
    for info in nflgame.sched.games.itervalues():
        y, t, w = info['year'], info['season_type'], info['week']
        h, a = info['home'], info['away']
        if year is not None:
            if isinstance(year, list) and y not in year:
                continue
            if not isinstance(year, list) and y != year:
                continue
        if week is not None:
            if isinstance(week, list) and w not in week:
                continue
            if not isinstance(week, list) and w != week:
                continue
        if home is not None and away is not None and home == away:
            if h != home and a != home:
                continue
        else:
            if home is not None and h != home:
                continue
            if away is not None and a != away:
                continue
        if t != kind:
            continue
        if started:
            gametime = nflgame.live._game_datetime(info)
            now = nflgame.live._now()
            if gametime > now and (gametime - now).total_seconds() > 300:
                continue
        infos.append(info)
    return infos
