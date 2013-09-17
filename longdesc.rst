nflgame is an API to retrieve and read NFL Game Center JSON data. It can
work with real-time data, which can be used for fantasy football.

nflgame works by parsing the same JSON data that powers NFL.com's live
GameCenter. Therefore, nflgame can be used to report game statistics
while a game is being played.

The package comes pre-loaded with game data from every pre- and regular
season game from 2009 up until the present (I try to update it every
week). Therefore, querying such data does not actually ping NFL.com.

However, if you try to search for data in a game that is being currently
played, the JSON data will be downloaded from NFL.com at each request
(so be careful not to inspect for data too many times while a game is
being played). If you ask for data for a particular game that hasn't
been cached to disk but is no longer being played, it will be
automatically cached to disk so that no further downloads are required.

Here's a quick teaser to find the top 5 running backs by rushing yards
in the first week of the 2013 season:

::

    #!python
    import nflgame

    games = nflgame.games(2013, week=1)
    players = nflgame.combine_game_stats(games)
    for p in players.rushing().sort('rushing_yds').limit(5):
        msg = '%s %d carries for %d yards and %d TDs'
        print msg % (p, p.rushing_att, p.rushing_yds, p.rushing_tds)

And the output is:

::

    L.McCoy 31 carries for 184 yards and 1 TDs
    T.Pryor 13 carries for 112 yards and 0 TDs
    S.Vereen 14 carries for 101 yards and 0 TDs
    A.Peterson 18 carries for 93 yards and 2 TDs
    R.Bush 21 carries for 90 yards and 0 TDs

Or you could find the top 5 passing plays in the same time period:

::

    #!python
    import nflgame

    games = nflgame.games(2013, week=1)
    plays = nflgame.combine_plays(games)
    for p in plays.sort('passing_yds').limit(5):
        print p

And the output is:

::

    (DEN, DEN 22, Q4, 3 and 8) (4:42) (Shotgun) P.Manning pass short left to D.Thomas for 78 yards, TOUCHDOWN. Penalty on BAL-E.Dumervil, Defensive Offside, declined.
    (DET, DET 23, Q3, 3 and 7) (5:58) (Shotgun) M.Stafford pass short middle to R.Bush for 77 yards, TOUCHDOWN.
    (NYG, NYG 30, Q2, 1 and 10) (2:01) (No Huddle, Shotgun) E.Manning pass deep left to V.Cruz for 70 yards, TOUCHDOWN. Pass complete on a fly pattern.
    (NO, NO 24, Q2, 2 and 6) (5:11) (Shotgun) D.Brees pass deep left to K.Stills to ATL 9 for 67 yards (R.McClain; R.Alford). Pass 24, YAC 43
    (NYG, NYG 20, Q1, 1 and 10) (13:04) E.Manning pass short middle to H.Nicks pushed ob at DAL 23 for 57 yards (M.Claiborne). Pass complete on a slant pattern.

If you aren't a programmer, then the `tutorial for non
programmers <https://github.com/BurntSushi/nflgame/wiki/Tutorial-for-non-programmers:-Installation-and-examples>`__
is for you.

If you need help, please come visit us at IRC/FreeNode on channel
``#nflgame``. If you've never used IRC before, then you can `use a web
client <http://webchat.freenode.net/?channels=%23nflgame>`__. (Enter any
nickname you like, make sure the channel is ``#nflgame``, fill in the
captcha and hit connect.)

Failing IRC, the second fastest way to get help is to `open a new issue
on the tracker <https://github.com/BurntSushi/nflgame/issues/new>`__.
There are several active contributors to nflgame that watch the issue
tracker. We tend to respond fairly quickly!
