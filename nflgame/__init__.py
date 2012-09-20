"""
Introduction
============
An API to retrieve and read NFL Game Center JSON data.
It can work with real-time data, which can be used for fantasy football.

nflgame works by parsing the same JSON data that powers NFL.com's live
GameCenter. Therefore, nflgame can be used to report game statistics while
a game is being played.

The package comes pre-loaded with game data from every pre- and regular
season game from 2009 up until August 28, 2012. Therefore, querying such data
does not actually ping NFL.com.

However, if you try to search for data in a game that is being currently
played, the JSON data will be downloaded from NFL.com at each request (so be
careful not to inspect for data too many times while a game is being played).
If you ask for data for a particular game that hasn't been cached to disk
but is no longer being played, it will be automatically cached to disk
so that no further downloads are required.

nflgame requires Python 2.6 or Python 2.7. It does not (yet) work with
Python 3.

Examples
========

Finding games
-------------
Games can be selected in bulk, e.g., every game in week 1 of 2010::

    games = nflgame.games(2010, week=1)

Or pin-pointed exactly, e.g., the Patriots week 17 whomping against the Bills::

    game = nflgame.game(2011, 17, "NE", "BUF")

This season's (2012) pre-season games can also be accessed::

    pregames = nflgame.games(2012, kind='PRE')

Find passing leaders of a game
------------------------------
Given some game, the player statistics can be easily searched. For example,
to find the passing leaders of a particular game::

    for p in game.players.passing().sort("passing_yds"):
        print p, p.passing_att, p.passing_cmp, p.passing_yds, p.passing_tds

Output::

    T.Brady 35 23 338 3
    R.Fitzpatrick 46 29 307 2
    B.Hoyer 1 1 22 0

See every player that made an interception
------------------------------------------
We can filter all players on whether they had more than zero defensive
interceptions, and then sort those players by the number of picks::

    for p in game.players.filter(defense_int=lambda x:x>0).sort("defense_int"):
        print p, p.defense_int

Output::

    S.Moore 2
    A.Molden 1
    D.McCourty 1
    N.Barnett 1

Finding weekly rushing leaders
------------------------------
Sequences of players can be added together, and their sum can then be used
like any other sequence of players. For example, to get every player
that played in week 10 of 2009::

    week10 = nflgame.games(2009, 10)
    players = nflgame.combine(week10)

And then to list all rushers with at least 10 carries sorted by rushing yards::

    rushers = players.rushing()
    for p in rushers.filter(rushing_att=lambda x: x > 10).sort("rushing_yds"):
        print p, p.rushing_att, p.rushing_yds, p.rushing_tds

And the final output::

    A.Peterson 18 133 2
    C.Johnson 26 132 2
    S.Jackson 26 131 1
    M.Jones-Drew 24 123 1
    J.Forsett 17 123 1
    M.Bush 14 119 0
    L.Betts 26 114 1
    F.Gore 25 104 1
    J.Charles 18 103 1
    R.Williams 20 102 0
    K.Moreno 18 97 0
    L.Tomlinson 24 96 2
    D.Williams 19 92 0
    R.Rice 20 89 1
    C.Wells 16 85 2
    J.Stewart 11 82 2
    R.Brown 12 82 1
    R.Grant 19 79 0
    K.Faulk 12 79 0
    T.Jones 21 77 1
    J.Snelling 18 61 1
    K.Smith 12 55 0
    C.Williams 14 52 1
    M.Forte 20 41 0
    P.Thomas 11 37 0
    R.Mendenhall 13 36 0
    W.McGahee 13 35 0
    B.Scott 13 33 0
    L.Maroney 13 31 1

You could do the same for the entire 2009 season::

    players = nflgame.combine(nflgame.games(2009))
    for p in players.rushing().sort("rushing_yds").limit(35):
        print p, p.rushing_att, p.rushing_yds, p.rushing_tds

And the output::

    C.Johnson 322 1872 12
    S.Jackson 305 1361 4
    A.Peterson 306 1335 17
    T.Jones 305 1324 12
    M.Jones-Drew 296 1309 15
    R.Rice 240 1269 7
    R.Grant 271 1202 10
    C.Benson 272 1118 6
    D.Williams 210 1104 7
    R.Williams 229 1090 11
    R.Mendenhall 222 1014 7
    F.Gore 206 1013 8
    J.Stewart 205 1008 9
    K.Moreno 233 897 5
    M.Turner 177 864 10
    J.Charles 165 861 5
    F.Jackson 205 850 2
    M.Barber 200 841 7
    B.Jacobs 218 834 5
    M.Forte 242 828 4
    J.Addai 213 788 9
    C.Williams 190 776 4
    C.Wells 170 774 7
    A.Bradshaw 156 765 7
    L.Maroney 189 735 9
    J.Harrison 161 735 4
    P.Thomas 141 733 5
    L.Tomlinson 221 729 12
    Kv.Smith 196 678 4
    L.McCoy 154 633 4
    M.Bell 155 626 5
    C.Buckhalter 114 624 1
    J.Jones 163 602 2
    F.Jones 101 594 2
    T.Hightower 137 574 8

Load data into Excel
--------------------
Every sequence of Players can be easily dumped into a file formatted
as comma-separated values (CSV). CSV files can then be opened directly
with programs like Excel, Google Docs, Open Office and Libre Office.

You could dump every statistic from a game like so::

    game.players.csv('player-stats.csv')

Or if you want to get crazy, you could dump the statistics of every player
from an entire season::

    nflgame.combine(nflgame.games(2010)).csv('season2010.csv')
"""

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict  # from PyPI
import itertools

import nflgame.game
import nflgame.live
import nflgame.player
import nflgame.schedule
import nflgame.seq

VERSION = "1.1.5"

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
    ['ATL', 'Atlanta', 'Falcons', 'Atlana Falcons'],
    ['BAL', 'Baltimore', 'Ravens', 'Baltimore Ravens'],
    ['BUF', 'Buffalo', 'Bills', 'Buffalo Bills'],
    ['CAR', 'Carolina', 'Panthers', 'Caroline Panthers'],
    ['CHI', 'Chicago', 'Bears', 'Chicago Bears'],
    ['CIN', 'Cincinnati', 'Bengals', 'Cincinnati Bengals'],
    ['CLE', 'Cleveland', 'Browns', 'Cleveland Browns'],
    ['DAL', 'Dallas', 'Cowboys', 'Dallas Cowboys'],
    ['DEN', 'Denver', 'Broncos', 'Denver Broncos'],
    ['DET', 'Detroit', 'Lions', 'Detroit Lions'],
    ['GB', 'Green Bay', 'Packers', 'Green Bay Packers', 'G.B.'],
    ['HOU', 'Houston', 'Texans', 'Houston Texans'],
    ['IND', 'Indianapolis', 'Colts', 'Indianapolis Colts'],
    ['JAC', 'Jacksonville', 'Jaguars', 'Jacksonville Jaguars', 'JAX'],
    ['KC', 'Kansas City', 'Chiefs', 'Kansas City Chiefs', 'K.C.'],
    ['MIA', 'Miami', 'Dolphins', 'Miami Dolphins'],
    ['MIN', 'Minnesota', 'Vikings', 'Minnesota Vikings'],
    ['NE', 'New England', 'Patriots', 'New England Patriots', 'N.E.'],
    ['NO', 'New Orleans', 'Saints', 'New Orleans Saints', 'N.O.'],
    ['NYG', 'Giants', 'New York Giants', 'N.Y.G.'],
    ['NYJ', 'Jets', 'New York Jets', 'N.Y.J.'],
    ['OAK', 'Oakland', 'Raiders', 'Oakland Raiders'],
    ['PHI', 'Philadelphia', 'Eagles', 'Philadelphia Eagles'],
    ['PIT', 'Pittsburgh', 'Steelers', 'Pittsburgh Steelers'],
    ['SD', 'San Diego', 'Chargers', 'San Diego Chargers', 'S.D.'],
    ['SEA', 'Seattle', 'Seahawks', 'Seattle Seahawks'],
    ['SF', 'San Francisco', '49ers', 'San Francisco 49ers', 'S.F.'],
    ['STL', 'St. Louis', 'Rams', 'St. Louis Rams', 'S.T.L.'],
    ['TB', 'Tampa Bay', 'Buccaneers', 'Tampa Bay Buccaneers', 'T.B.'],
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
    for (y, t, w, h, a), info in nflgame.schedule.games:
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
