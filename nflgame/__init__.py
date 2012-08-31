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

Examples
========

Finding games
-------------
Games can be selected in bulk, e.g., every game in week 1 of 2010::

    games = nflgame.games(2010, week=1)

Or pin-pointed exactly, e.g., the Patriots week 17 whomping against the Bills::

    game = nflgame.game(2011, 17, "NE", "BUF")

This season's (2012) pre-season games can also be accessed::

    pregames = nflgame.games(2012, preseason=True)

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

from collections import OrderedDict

import nflgame.game as game
import nflgame.player as player
import nflgame.schedule as schedule

VERSION = "1.0.4"

NoPlayers = player.Players(None)
"""
NoPlayers corresponds to the identity element of a Players sequences.

Namely, adding it to any other Players sequence has no effect.
"""


def games(year, week=None, home=None, away=None, preseason=False):
    """
    games returns a list of all games matching the given criteria. Each
    game can then be queried for player statistics and information about
    the game itself (score, winner, scoring plays, etc.).

    Note that if a game's JSON data is not cached to disk, it is retrieved
    from the NFL web site. A game's JSON data is *only* cached to disk once
    the game is over, so be careful with the number of times you call this
    while a game is going on. (i.e., don't piss off NFL.com.)
    """
    eids = __search_schedule(year, week, home, away, preseason)
    if not eids:
        return None
    return [game.Game(eid) for eid in eids]


def one(year, week, home, away, preseason=False):
    """
    one returns a single game matching the given criteria. The
    game can then be queried for player statistics and information about
    the game itself (score, winner, scoring plays, etc.).

    one returns either a single game or no games. If there are multiple games
    matching the given criteria, an assertion is raised.

    Note that if a game's JSON data is not cached to disk, it is retrieved
    from the NFL web site. A game's JSON data is *only* cached to disk once
    the game is over, so be careful with the number of times you call this
    while a game is going on. (i.e., don't piss off NFL.com.)
    """
    eids = __search_schedule(year, week, home, away, preseason)
    if not eids:
        return None
    assert len(eids) == 1, 'More than one game matches the given criteria.'
    return game.Game(eids[0])


def combine(games):
    """
    Combines a list of games into one big player sequence.

    This can be used, for example, to get Player objects corresponding to
    statistics across an entire week, some number of weeks or an entire season.
    """
    players = OrderedDict()
    for game in games:
        for p in game.players:
            if p.playerid not in players:
                players[p.playerid] = p
            else:
                players[p.playerid] += p
    return player.Players(players)


def __search_schedule(year, week=None, home=None, away=None, preseason=False):
    """
    Searches the schedule to find the game identifiers matching the criteria
    given.
    """
    ids = []
    for (y, t, w, h, a), info in schedule.games:
        if y != year:
            continue
        if week is not None:
            if isinstance(week, list) and w not in week:
                continue
            if not isinstance(week, list) and w != week:
                continue
        if home is not None and h != home:
            continue
        if away is not None and a != away:
            continue
        if preseason and t != "PRE":
            continue
        if not preseason and t != "REG":
            continue
        ids.append(info['eid'])
    return ids
