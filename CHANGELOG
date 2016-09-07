1.2.20
======
  - Updates for the 2016 season.

1.2.19
======
  - Fix nfldb/#134.
  - Data updates.

1.2.17
======
  - Fix #157.

1.2.16
======
  - Fix #150.
  - Data updates.

1.2.15
======
  - Data updates.

1.2.14
======
  - Data updates.

1.2.13
======
  - Fixed future import from #109.
  - Player DB update.

1.2.12
======
  - Added function to compute QB passer rating (#109).
    Contributed by @monstermudder78.

1.2.11
======
  - Player + schedule + game update.

1.2.10
======
  - Switch over to post-season schedule (fixes #106).
  - Player + schedule + game update.

1.2.9
=====
  - Player + schedule + game update.

1.2.8
=====
  - Fix #95.
  - Player + schedule update.

1.2.7
=====
  - Player and preseason 2014 game updates.
  - Better error reporting when scraping rosters to help debug nfldb#47.

1.2.6
=====
  - Support hall-of-fame games, and add all HOF games back to 2009.
  - Player and schedule updates.
  - Switch nflgame.live back to regular season mode.

1.2.5
=====
  - Add data from Super Bowl.
  - Player DB update.

1.2.4
=====
  - Fixed a bug in nflgame.live where the season phase was being
    incorrectly determined when the next game was the pro bowl.
  - Schedule update for Super Bowl.

1.2.3
=====
  - Player and schedule updates.
  - Game data for divisional round of 2013 playoffs.
  - Merge PR #71 that fixes a bug in nflgame-update-players.
    (The current season phase should only be accessed a call to
     nflgame.live.current_year_and_week().)

1.2.2
=====
  - Player DB update.
  - Fix schedule so that post-season games in Jan/Feb belong to the
    right season year. (e.g., Games in 01/2014 are in the 2013 season.)

1.2.1
=====
  - Some touchups made to the formatting of the JSON file so that
    it is diff friendly.

1.2.0
=====
  - Schedule data has been moved to JSON, and it now automatically
    updates.
    It can also be updated manually with the new script
    `nflgame-update-schedule`.

1.1.31
======
  - Fix a bug in nflgame.live where the playoff week was being
    reported as 18, 19, ... instead of 1, 2, ...
    This also fixes the nflgame-update-players script.
  - Player DB update.

1.1.30
======
  - Game data for wild card round (2013).
  - Schedule update for divisional playoffs (2013).

1.1.29
======
  - Schedule update (PR #68).
  - Player DB update.
  - Game updates through week 17 of 2013 season.
  - Change schedule URL in nflgame.live to the postseason
    schedule.

1.1.28
======
  - Fix issue #65.
  - Schedule update.
  - Player DB update.
  - Game updates through week 16 of 2013 season.

1.1.27
======
  - Player DB update.
  - Game updates through first game of week 15 of 2013 season.
  - Schedule update (pats got bumped from SNF in week 16).
  - Update documentation for `nflgame.live.run`.

1.1.26
======
  - Fixed corrupt 2013120806 game file.
  - Added game data for most games in week 14 of 2013 season.
  - Player DB updated.
  - NFL schedule updated.

1.1.25
======
  - Merged front9tech's pull request (#58) that is more forgiving toward
    errant JSON data.
  - Player JSON database update.
  - Game data updates.

1.1.24
======
  - Fix issue #55. Better data sanitization for colleges.

1.1.23
======
  - Sanitize height data in the JSON player database. It is
    all converted to inches.
  - Game and player database updates.

1.1.22
======
  - No longer depend on a specific version of pytz.
  - Player database update.
  - Game update.
  - Schedule update.

1.1.21
======
  - Expunge errant drives from games.

1.1.20
======
  - Fix a bug where drives with no plays (a bug in the source data)
    causes loading a drive to crash your program.
  - Player database update.

1.1.19
======
  - Windows can't handle symlinks in setup.py.

1.1.18
======
  - Switched to a more "professional" UNLICENCE.
    (There are no practical differences from the WTFPL.)
  - Player database update and first game of week 3.
  - Moved nflgame-update-players to its own module. (Fixes issue #43.)

1.1.17
======
  - Make the PyPI page look nicer.

1.1.16
======
  - Player database updates.
  - Weeks 1 and 2 of the 2013 regular season.
  - Fixed a bug with getting the uniform number from the JSON file.
  - Fixed embarrassing team name misspellings. (issue #41)
  - Cleaned up setup.py dependencies and got smarter about requiring
    argparse and ordereddict from PyPI.
  - Set a timeout on updating the current season week so it doesn't
    hang forever.
  - A total rewrite of the README to reflect API updates, the new IRC
    channel, and teasers about other projects.

1.1.15
======
  - Player database updates.
  - Changed the player update script to stay fresh on position and status
    data (in addition to team data). Namely, if the attributes become
    unavailable, then they should be empty, regardless of their previous
    values.
  - Changed the `csv` import to be local to the csv export function as a
    bandaide for QPython on Android (see issue #32).
  - Expose player identifiers as `gsis_id` in addition to `player_id`.

1.1.14
======
  - Data updates for preseason weeks 2-4 (4 isn't complete yet).
  - A complete rewrite of the JSON player database. Meta data is
    now much more complete (with the vast majority of every player
    in nflgame data back to 2009 having some meta data). Also,
    nflgame now includes a `nflgame-update-players` script to
    update the JSON player database using a minimal number of
    HTTP requests.
  - Use `tsv` extension so GitHub shows test results better.
  - Recover gracefully if there is a socket timeout when downloading
    JSON data.

1.1.13
======
  - Mostly a maintenance release with some reorganization.
    I'm beginning migration to a new documentation tool `pdoc`.

1.1.12
======
  - Fixed a bug where `nflgame.live` was not properly interpreting
    the phase of the season. (It thought it was always the regular
    season.) Now it should automatically infer preseason, regular
    season or postseason.

1.1.11
======
  - Update schedule for the 2013 preseason and regular season.
  - Updated the players.json meta data file.
  - Added nflgame's first test. It compares aggregate statistics
    from 2012 against statistics reported by Yahoo. Overall, the
    prognosis is good, but there are definitely some inaccuracies.
    But I do think `nflgame` is doing the best it can without
    another source. Look in `test-data` for test results and look
    in `scripts/compare-with-yahoo` for more details on the
    methodology.
  - Added some more team abbreviations from Yahoo. (Weird ones.)
  - Added a method to player objects to guess their position
    based on available statistics.
  - Corrected a few typos (or artifacts from old names) in the
    `nflgame.statmap` module.

1.1.10
======
  - Make the FieldPosition type constructor more accepting of
    different inputs. e.g., an integer. Also, added an add_yards
    method to FieldPosition that returns a new FieldPosition
    with the given yards added to it.
  - Make the default string representation of a game unambiguous.
  - Modified the quarter numbering correction of drives to be
    smarter by looking at all plays of a drive instead of just
    the last one.
  - Modified the play duplication logic to be heuristically smarter.
    Namely, instead of just looking at play ids, nflgame now
    inspects play data to see if two plays are semantically
    equivalent. This was necessary because duplicate plays could
    have different ids.
  - Manually corrected some seriously corrupt data in the
    Week 13 match up DET at NO. Also updated a couple other
    games from 2012 with updates from upstream.
  - Updated players.json with most recent player meta data.


1.1.9
=====
  - Manually fixed the ATL/SF 2012 playoff game so that it
    reports itself as being "over".
  - Make the license field in setup.py accurate.
  - Added "gamekey" or "gsis" identifiers to nflgame's
    schedule data. These ids are used in other services,
    like Neulion's content delivery network.
  - Added a method to the Game class that returns the season
    year that the game was played. In particular, games
    played in January or February of 2013 will still return
    2012.
  - Added a new "schedule" field to the Game class which contains
    the meta data in nflgame/schedule.py.


1.1.8
=====
Data updates:

  - Schedule (end of 2012 postseason)
  - README inconsistency.
  - Make the CSV function output consistent column headings/ordering.


1.1.7
=====
Data updates:

  - Player database (end of 2012 regular season)
  - Game data (full 2012 regular season)
  - Game schedule up to first week of 2012 postseason


1.1.6
=====
Data update. And made parsing game times a bit more robust with respect to
errant or malformed data.


1.1.5
=====
Added player team and position information to CSV output. Team information
should always be available, but position information is dependent on whether
or not the player meta data exists for that particular player. (Chances are
good.)


1.1.4
=====
Bug fixes and added game diffs to the nflgame.live callback API.

- Fixed a bug where Game.max_player_stats didn't include statistics from
  players that only had stats recorded in play-by-play data.

- When player stats are combined over a game or multiple games, keep the 'home'
  attribute if the two objects agree on its value.

- Added Week 2 data from the 2012 season.

- The callback function used in the nflgame.live module now requires a third
  parameter: a list of diffs between the games reported in the last interval
  and the games reported in the current interval. It is hopefully useful in
  inspecting statistics and plays that have been added or changed since the
  last inspection of the game data. (The diffs list is orthogonal to the first
  two parameters: active and completed.)

- Fixed bug #14. Games that hadn't started yet weren't filtered out of the
  return list of nflgame.games and related functions.

- Fixed a bug where if JSON data from NFL.com is totally unparseable, then we
  return None when constructing a Game object rather than crash the program.

- Added a team attribute to PlayerStats objects.

- When filtering by a particular field, if that fields value is None, then
  always return False.


1.1.3
=====
Bug fixes.

- Fixed a bug that made pytz a hard dependency when importing nflgame.


1.1.2
=====
Added a couple of convenience methods to the API and fixed a few bugs.

- Added a 'started' parameter to nflgame.{games,games_gen,one} that when set,
  will only return games that have already started or will start in five
  minutes. This is useful for preemptying 404 errors that may be too costly.

- Added a max_player_stats method to the Game class. It works by combining
  player statistics reported at the game level and player statistics reported
  at the play level. Each statistic is combined by taking the max of each
  value. (This is a heuristic designed to mitigate errors in the GameCenter
  JSON data. It is not perfect.)

- Deprecated the nflgame.combine function. It has been replaced by three
  different ways of combining player data across games: combine game level
  player statistics with nflgame.combine_game_stats, combine play level
  player statistics with nflgame.combine_play_stats and combine the maximum
  of game and play level statistics with nflgame.combine_max_stats.

- Added three two point conversion properties to player stats objects: twopta,
  twoptm and twoptmissed. These group the two point conversion statistics that
  exist only as individual passing, rushing and receiving statistics.

- Fixed a bug in the main sequence generator where decorated properties
  could not be used as a field in 'filter'. (i.e., use 'getattr' instead of
  accessing '__dict__' directly.)

- Fixed bug 9. (Updated PlayerStats.csv to work with recent API changes.)

- Added a 'defense_tds' statistical field in the nflgame.statmap module for
  convenience purposes.

