from collections import namedtuple
import os
import os.path as path
import gzip
import json
import socket
import sys
import urllib2

from nflgame import OrderedDict
import nflgame.player
import nflgame.sched
import nflgame.seq
import nflgame.statmap

_MAX_INT = sys.maxint

_jsonf = path.join(path.split(__file__)[0], 'gamecenter-json', '%s.json.gz')
_json_base_url = "http://www.nfl.com/liveupdate/game-center/%s/%s_gtd.json"

GameDiff = namedtuple('GameDiff', ['before', 'after', 'plays', 'players'])
"""
Represents the difference between two points in time of the same game
in terms of plays and player statistics.
"""

TeamStats = namedtuple('TeamStats',
                       ['first_downs', 'total_yds', 'passing_yds',
                        'rushing_yds', 'penalty_cnt', 'penalty_yds',
                        'turnovers', 'punt_cnt', 'punt_yds', 'punt_avg',
                        'pos_time'])
"""A collection of team statistics for an entire game."""


class FieldPosition (object):
    """
    Represents field position.

    The representation here is an integer offset where the 50 yard line
    corresponds to '0'. Being in the own territory corresponds to a negative
    offset while being in the opponent's territory corresponds to a positive
    offset.

    e.g., NE has the ball on the NE 45, the offset is -5.
    e.g., NE has the ball on the NYG 2, the offset is 48.

    This representation allows for gains in any particular play to be added
    to the field offset to get the new field position as the result of the
    play.
    """
    def __new__(cls, pos_team=None, yardline=None, offset=None):
        if not yardline and offset is None:
            return None
        return object.__new__(cls)

    def __init__(self, pos_team=None, yardline=None, offset=None):
        """
        pos_team is the team on offense, and yardline is a string formatted
        like 'team-territory yard-line'. e.g., "NE 32".

        An offset can be given directly by specifying an integer for offset.
        """
        if isinstance(offset, int):
            self.offset = offset
            return
        if yardline == '50':
            self.offset = 0
            return

        territory, yd_str = yardline.split()
        yd = int(yd_str)
        if territory == pos_team:
            self.offset = -(50 - yd)
        else:
            self.offset = 50 - yd

    def __cmp__(self, other):
        if isinstance(other, int):
            return cmp(self.offset, other)
        return cmp(self.offset, other.offset)

    def __str__(self):
        if self.offset > 0:
            return 'OPP %d' % (50 - self.offset)
        elif self.offset < 0:
            return 'OWN %d' % (50 + self.offset)
        else:
            return 'MIDFIELD'

    def add_yards(self, yards):
        """
        Returns a new field position with the yards added to self.
        Yards may be negative.
        """
        newoffset = max(-50, min(50, self.offset + yards))
        return FieldPosition(offset=newoffset)


class PossessionTime (object):
    """
    Represents the amount of time a drive lasted in (minutes, seconds).
    """
    def __init__(self, clock):
        self.clock = clock

        try:
            self.minutes, self.seconds = map(int, self.clock.split(':'))
        except ValueError:
            self.minutes, self.seconds = 0, 0

    def total_seconds(self):
        """
        Returns the total number of seconds that this possession lasted for.
        """
        return self.seconds + self.minutes * 60

    def __cmp__(self, other):
        a, b = (self.minutes, self.seconds), (other.minutes, other.seconds)
        return cmp(a, b)

    def __add__(self, other):
        new_time = PossessionTime('0:00')
        total_seconds = self.total_seconds() + other.total_seconds()
        new_time.minutes = total_seconds / 60
        new_time.seconds = total_seconds % 60
        new_time.clock = '%.2d:%.2d' % (new_time.minutes, new_time.seconds)
        return new_time

    def __sub__(self, other):
        assert self >= other
        new_time = PossessionTime('0:00')
        total_seconds = self.total_seconds() - other.total_seconds()
        new_time.minutes = total_seconds / 60
        new_time.seconds = total_seconds % 60
        new_time.clock = '%.2d:%.2d' % (new_time.minutes, new_time.seconds)
        return new_time

    def __str__(self):
        return self.clock


class GameClock (object):
    """
    Represents the current time in a game. Namely, it keeps track of the
    quarter and clock time. Also, GameClock can represent whether
    the game hasn't started yet, is half time or if it's over.
    """
    def __init__(self, qtr, clock):
        self.qtr = qtr
        self.clock = clock

        try:
            self._minutes, self._seconds = map(int, self.clock.split(':'))
        except ValueError:
            self._minutes, self._seconds = 0, 0
        except AttributeError:
            self._minutes, self._seconds = 0, 0
        try:
            self.__qtr = int(self.qtr)
            if self.__qtr >= 3:
                self.__qtr += 1  # Let halftime be quarter 3
        except ValueError:
            if self.is_pregame():
                self.__qtr = 0
            elif self.is_halftime():
                self.__qtr = 3
            elif self.is_final():
                self.__qtr = sys.maxint
            else:
                self.qtr = 'Pregame'

    @property
    def quarter(self):
        return self.__qtr

    @quarter.setter
    def quarter(self, value):
        if isinstance(value, int):
            assert value >= 0 and value <= 4
            self.qtr = str(value)
            self.__qtr = value
        else:
            self.qtr = value
            self.__qtr = 0

    def is_pregame(self):
        return self.qtr == 'Pregame'

    def is_halftime(self):
        return self.qtr == 'Halftime'

    def is_final(self):
        return 'final' in self.qtr.lower()

    def __cmp__(self, other):
        if self.__qtr != other.__qtr:
            return cmp(self.__qtr, other.__qtr)
        elif self._minutes != other._minutes:
            return cmp(other._minutes, self._minutes)
        return cmp(other._seconds, self._seconds)

    def __str__(self):
        """
        Returns a nicely formatted string indicating the current time of the
        game. Examples include "Q1 10:52", "Q4 1:25", "Pregame", "Halftime"
        and "Final".
        """
        try:
            q = int(self.qtr)
            return 'Q%d %s' % (q, self.clock)
        except ValueError:
            return self.qtr


class Game (object):
    """
    Game represents a single pre- or regular-season game. It provides a window
    into the statistics of every player that played into the game, along with
    the winner of the game, the score and a list of all the scoring plays.
    """

    def __new__(cls, eid=None, fpath=None):
        # If we can't get a valid JSON data, exit out and return None.
        try:
            rawData = _get_json_data(eid, fpath)
        except urllib2.URLError:
            return None
        if rawData is None or rawData.strip() == '{}':
            return None
        game = object.__new__(cls)
        game.rawData = rawData

        try:
            if eid is not None:
                game.eid = eid
                game.data = json.loads(game.rawData)[game.eid]
            else:  # For when we have rawData (fpath) and no eid.
                game.eid = None
                game.data = json.loads(game.rawData)
                for k, v in game.data.iteritems():
                    if isinstance(v, dict):
                        game.eid = k
                        game.data = v
                        break
                assert game.eid is not None
        except ValueError:
            return None

        return game

    def __init__(self, eid=None, fpath=None):
        """
        Creates a new Game instance given a game identifier.

        The game identifier is used by NFL.com's GameCenter live update web
        pages. It is used to construct a URL to download JSON data for the
        game.

        If the game has been completed, the JSON data will be cached to disk
        so that subsequent accesses will not re-download the data but instead
        read it from disk.

        When the JSON data is written to disk, it is compressed using gzip.
        """
        # Make the schedule info more accessible.
        self.schedule = nflgame.sched.games.get(self.eid, None)

        # Home and team cumulative statistics.
        self.home = self.data['home']['abbr']
        self.away = self.data['away']['abbr']
        self.stats_home = _json_team_stats(self.data['home']['stats']['team'])
        self.stats_away = _json_team_stats(self.data['away']['stats']['team'])

        # Load up some simple static values.
        self.gamekey = nflgame.sched.games[self.eid]['gamekey']
        self.time = GameClock(self.data['qtr'], self.data['clock'])
        self.down = _tryint(self.data['down'])
        self.togo = _tryint(self.data['togo'])
        self.score_home = int(self.data['home']['score']['T'])
        self.score_away = int(self.data['away']['score']['T'])
        for q in (1, 2, 3, 4, 5):
            for team in ('home', 'away'):
                score = self.data[team]['score'][str(q)]
                self.__dict__['score_%s_q%d' % (team, q)] = int(score)

        if not self.game_over():
            self.winner = None
        else:
            if self.score_home > self.score_away:
                self.winner = self.home
                self.loser = self.away
            elif self.score_away > self.score_home:
                self.winner = self.away
                self.loser = self.home
            else:
                self.winner = '%s/%s' % (self.home, self.away)
                self.loser = '%s/%s' % (self.home, self.away)

        # Load the scoring summary into a simple list of strings.
        self.scores = []
        for k in sorted(map(int, self.data['scrsummary'])):
            play = self.data['scrsummary'][str(k)]
            s = '%s - Q%d - %s - %s' \
                % (play['team'], play['qtr'], play['type'], play['desc'])
            self.scores.append(s)

        # Check to see if the game is over, and if so, cache the data.
        if self.game_over() and not os.access(_jsonf % eid, os.R_OK):
            self.save()

    def is_home(self, team):
        """Returns true if team (i.e., 'NE') is the home team."""
        return team == self.home

    def season(self):
        """Returns the year of the season this game belongs to."""
        year = int(self.eid[0:4])
        month = int(self.eid[4:6])
        if month <= 3:
            year -= 1
        return year

    def game_over(self):
        """game_over returns true if the game is no longer being played."""
        return self.time.is_final()

    def playing(self):
        """playing returns true if the game is currently being played."""
        return not self.time.is_pregame() and not self.time.is_final()

    def save(self, fpath=None):
        """
        Save the JSON data to fpath. This is done automatically if the
        game is over.
        """
        if fpath is None:
            fpath = _jsonf % self.eid
        try:
            print >> gzip.open(fpath, 'w+'), self.rawData,
        except IOError:
            print >> sys.stderr, "Could not cache JSON data. Please " \
                                 "make '%s' writable." \
                                 % os.path.dirname(fpath)

    def nice_score(self):
        """
        Returns a string of the score of the game.
        e.g., "NE (32) vs. NYG (0)".
        """
        return '%s (%d) at %s (%d)' \
               % (self.away, self.score_away, self.home, self.score_home)

    def max_player_stats(self):
        """
        Returns a GenPlayers sequence of player statistics that combines
        game statistics and play statistics by taking the max value of
        each corresponding statistic.

        This is useful when accuracy is desirable. Namely, using only
        play-by-play data or using only game statistics can be unreliable.
        That is, both are inconsistently correct.

        Taking the max values of each statistic reduces the chance of being
        wrong (particularly for stats that are in both play-by-play data
        and game statistics), but does not eliminate them.
        """
        game_players = list(self.players)
        play_players = list(self.drives.plays().players())
        max_players = OrderedDict()

        # So this is a little tricky. It's possible for a player to have
        # only statistics at the play level, and therefore not be represented
        # in the game level statistics. Therefore, we initialize our
        # max_players with play-by-play stats first. Then go back through
        # and combine them with available game statistics.
        for pplay in play_players:
            newp = nflgame.player.GamePlayerStats(pplay.playerid,
                                                  pplay.name, pplay.home,
                                                  pplay.team)
            maxstats = {}
            for stat, val in pplay._stats.iteritems():
                maxstats[stat] = val

            newp._overwrite_stats(maxstats)
            max_players[pplay.playerid] = newp

        for newp in max_players.itervalues():
            for pgame in game_players:
                if pgame.playerid != newp.playerid:
                    continue

                maxstats = {}
                for stat, val in pgame._stats.iteritems():
                    maxstats[stat] = max([val,
                                          newp._stats.get(stat, -_MAX_INT)])

                newp._overwrite_stats(maxstats)
                break
        return nflgame.seq.GenPlayerStats(max_players)

    def __getattr__(self, name):
        if name == 'players':
            self.__players = _json_game_player_stats(self, self.data)
            self.players = nflgame.seq.GenPlayerStats(self.__players)
            return self.players
        if name == 'drives':
            self.__drives = _json_drives(self, self.home, self.data['drives'])
            self.drives = nflgame.seq.GenDrives(self.__drives)
            return self.drives
        raise AttributeError

    def __sub__(self, other):
        return diff(other, self)

    def __str__(self):
        return self.nice_score()


def diff(before, after):
    """
    Returns the difference between two points of time in a game in terms of
    plays and player statistics. The return value is a GameDiff namedtuple
    with two attributes: plays and players. Each contains *only* the data
    that is in the after game but not in the before game.

    This is useful for sending alerts where you're guaranteed to see each
    play statistic only once (assuming NFL.com behaves itself).
    """
    assert after.eid == before.eid

    plays = []
    after_plays = list(after.drives.plays())
    before_plays = list(before.drives.plays())
    for play in after_plays:
        if play not in before_plays:
            plays.append(play)

    # You might think that updated play data is enough. You could scan
    # it for statistics you're looking for (like touchdowns).
    # But sometimes a play can sneak in twice if its description gets
    # updated (late call? play review? etc.)
    # Thus, we do a diff on the play statistics for player data too.
    _players = OrderedDict()
    after_players = list(after.max_player_stats())
    before_players = list(before.max_player_stats())
    for aplayer in after_players:
        has_before = False
        for bplayer in before_players:
            if aplayer.playerid == bplayer.playerid:
                has_before = True
                pdiff = aplayer - bplayer
                if pdiff is not None:
                    _players[aplayer.playerid] = pdiff
        if not has_before:
            _players[aplayer.playerid] = aplayer
    players = nflgame.seq.GenPlayerStats(_players)

    return GameDiff(before=before, after=after, plays=plays, players=players)


class Drive (object):
    """
    Drive represents a single drive in an NFL game. It contains a list
    of all plays that happened in the drive, in chronological order.
    It also contains meta information about the drive such as the start
    and stop times and field position, length of possession, the number
    of first downs and a short descriptive string of the result of the
    drive.
    """
    def __init__(self, game, drive_num, home_team, data):
        if data is None or 'plays' not in data or len(data['plays']) == 0:
            return
        self.game = game
        self.drive_num = drive_num
        self.team = data['posteam']
        self.home = self.team == home_team
        self.first_downs = int(data['fds'])
        self.result = data['result']
        self.penalty_yds = int(data['penyds'])
        self.total_yds = int(data['ydsgained'])
        self.pos_time = PossessionTime(data['postime'])
        self.play_cnt = int(data['numplays'])
        self.field_start = FieldPosition(self.team, data['start']['yrdln'])
        self.time_start = GameClock(data['start']['qtr'],
                                    data['start']['time'])

        # When the game is over, the yardline isn't reported. So find the
        # last play that does report a yardline.
        if data['end']['yrdln'].strip():
            self.field_end = FieldPosition(self.team, data['end']['yrdln'])
        else:
            self.field_end = None
            playids = sorted(map(int, data['plays'].keys()), reverse=True)
            for pid in playids:
                yrdln = data['plays'][str(pid)]['yrdln'].strip()
                if yrdln:
                    self.field_end = FieldPosition(self.team, yrdln)
                    break
            if self.field_end is None:
                self.field_end = FieldPosition(self.team, '50')

        # When a drive lasts from Q1 to Q2 or Q3 to Q4, the 'end' doesn't
        # seem to change to the proper quarter. So scan all of the plays
        # and use the maximal quarter listed. (Just taking the last doesn't
        # seem to always work.)
        # lastplayid = str(max(map(int, data['plays'].keys())))
        # endqtr = data['plays'][lastplayid]['qtr']
        qtrs = [p['qtr'] for p in data['plays'].values()]
        maxq = str(max(map(int, qtrs)))
        self.time_end = GameClock(maxq, data['end']['time'])

        # One last sanity check. If the end time is less than the start time,
        # then bump the quarter if it seems reasonable.
        # This technique will blow up if a drive lasts more than fifteen
        # minutes and the quarter numbering is messed up.
        if self.time_end <= self.time_start \
                and self.time_end.quarter in (1, 3):
            self.time_end.quarter += 1

        self.__plays = _json_plays(self, data['plays'])
        self.plays = nflgame.seq.GenPlays(self.__plays)

    def __add__(self, other):
        """
        Adds the statistics of two drives together.

        Note that once two drives are added, the following fields
        automatically get None values: result, field_start, field_end,
        time_start and time_end.
        """
        assert self.team == other.team, \
            'Cannot add drives from different teams "%s" and "%s".' \
            % (self.team, other.team)
        new_drive = Drive(None, 0, '', None)
        new_drive.team = self.team
        new_drive.home = self.home
        new_drive.first_downs = self.first_downs + other.first_downs
        new_drive.penalty_yds = self.penalty_yds + other.penalty_yds
        new_drive.total_yds = self.total_yds + other.total_yds
        new_drive.pos_time = self.pos_time + other.pos_time
        new_drive.play_cnt = self.play_cnt + other.play_cnt
        new_drive.__plays = self.__plays + other.__plays
        new_drive.result = None
        new_drive.field_start = None
        new_drive.field_end = None
        new_drive.time_start = None
        new_drive.time_end = None
        return new_drive

    def __str__(self):
        return '%s (Start: %s, End: %s) %s' \
               % (self.team, self.time_start, self.time_end, self.result)


class Play (object):
    """
    Play represents a single play. It contains a list of all players
    that participated in the play (including offense, defense and special
    teams). The play also includes meta information about what down it
    is, field position, clock time, etc.

    Play objects also contain team-level statistics, such as whether the
    play was a first down, a fourth down failure, etc.
    """
    def __init__(self, drive, playid, data):
        self.data = data
        self.drive = drive
        self.playid = playid
        self.team = data['posteam']
        self.home = self.drive.home
        self.desc = data['desc']
        self.note = data['note']
        self.down = int(data['down'])
        self.yards_togo = int(data['ydstogo'])
        self.touchdown = 'touchdown' in self.desc.lower()
        self._stats = {}

        if not self.team:
            self.time, self.yardline = None, None
        else:
            self.time = GameClock(data['qtr'], data['time'])
            self.yardline = FieldPosition(self.team, data['yrdln'])

        # Load team statistics directly into the Play instance.
        # Things like third down attempts, first downs, etc.
        if '0' in data['players']:
            for info in data['players']['0']:
                if info['statId'] not in nflgame.statmap.idmap:
                    continue
                statvals = nflgame.statmap.values(info['statId'],
                                                  info['yards'])
                for k, v in statvals.iteritems():
                    v = self.__dict__.get(k, 0) + v
                    self.__dict__[k] = v
                    self._stats[k] = v

        # Load the sequence of "events" in a play into a list of dictionaries.
        self.events = _json_play_events(data['players'])

        # Now load cumulative player data for this play into
        # a GenPlayerStats generator. We then flatten this data
        # and add it to the play itself so that plays can be
        # filter by these statistics.
        self.__players = _json_play_players(self, data['players'])
        self.players = nflgame.seq.GenPlayerStats(self.__players)
        for p in self.players:
            for k, v in p.stats.iteritems():
                # Sometimes we may see duplicate statistics (like tackle
                # assists). Let's just overwrite in this case, since this
                # data is from the perspective of the play. i.e., there
                # is one assisted tackle rather than two.
                self.__dict__[k] = v
                self._stats[k] = v

    def has_player(self, playerid):
        """Whether a player with id playerid participated in this play."""
        return playerid in self.__players

    def __str__(self):
        if self.team:
            if self.down != 0:
                return '(%s, %s, Q%d, %d and %d) %s' \
                       % (self.team, self.data['yrdln'], self.time.qtr,
                          self.down, self.yards_togo, self.desc)
            else:
                return '(%s, %s, Q%d) %s' \
                       % (self.team, self.data['yrdln'], self.time.qtr,
                          self.desc)
        return self.desc

    def __eq__(self, other):
        """
        We use the play description to determine equality because the
        play description can be changed. (Like when a play is reversed.)
        """
        return self.playid == other.playid and self.desc == other.desc

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError
        return 0


def _json_team_stats(data):
    """
    Takes a team stats JSON entry and converts it to a TeamStats namedtuple.
    """
    return TeamStats(
        first_downs=int(data['totfd']),
        total_yds=int(data['totyds']),
        passing_yds=int(data['pyds']),
        rushing_yds=int(data['ryds']),
        penalty_cnt=int(data['pen']),
        penalty_yds=int(data['penyds']),
        turnovers=int(data['trnovr']),
        punt_cnt=int(data['pt']),
        punt_yds=int(data['ptyds']),
        punt_avg=int(data['ptavg']),
        pos_time=PossessionTime(data['top']))


def _json_drives(game, home_team, data):
    """
    Takes a home or away JSON entry and converts it to a list of Drive
    objects.
    """
    drive_nums = []
    for drive_num in data:
        try:
            drive_nums.append(int(drive_num))
        except:
            pass
    drives = []
    for i, drive_num in enumerate(sorted(drive_nums), 1):
        d = Drive(game, i, home_team, data[str(drive_num)])
        if not hasattr(d, 'game'):  # not a valid drive
            continue
        drives.append(d)
    return drives


def _json_plays(drive, data):
    """
    Takes a single JSON drive entry (data) and converts it to a list
    of Play objects. This includes trying to resolve duplicate play
    conflicts by only taking the first instance of a play.
    """
    plays = []
    seen_ids = set()
    seen_desc = set()  # Sometimes duplicates have different play ids...
    for playid in map(str, sorted(map(int, data))):
        p = data[playid]
        desc = (p['desc'], p['time'], p['yrdln'], p['qtr'])
        if playid in seen_ids or desc in seen_desc:
            continue
        seen_ids.add(playid)
        seen_desc.add(desc)
        plays.append(Play(drive, playid, data[playid]))
    return plays


def _json_play_players(play, data):
    """
    Takes a single JSON play entry (data) and converts it to an OrderedDict
    of player statistics.

    play is the instance of Play that this data is part of. It is used
    to determine whether the player belong to the home team or not.
    """
    players = OrderedDict()
    for playerid, statcats in data.iteritems():
        if playerid == '0':
            continue
        for info in statcats:
            if info['statId'] not in nflgame.statmap.idmap:
                continue
            if playerid not in players:
                home = play.drive.game.is_home(info['clubcode'])
                if home:
                    team_name = play.drive.game.home
                else:
                    team_name = play.drive.game.away
                stats = nflgame.player.PlayPlayerStats(playerid,
                                                       info['playerName'],
                                                       home, team_name)
                players[playerid] = stats
            statvals = nflgame.statmap.values(info['statId'], info['yards'])
            players[playerid]._add_stats(statvals)
    return players


def _json_play_events(data):
    """
    Takes a single JSON play entry (data) and converts it to a list of events.
    """
    temp = list()
    for playerid, statcats in data.iteritems():
        for info in statcats:
            if info['statId'] not in nflgame.statmap.idmap:
                continue
            statvals = nflgame.statmap.values(info['statId'], info['yards'])
            statvals['playerid'] = None if playerid == '0' else playerid
            statvals['playername'] = info['playerName'] or None
            statvals['team'] = info['clubcode']
            temp.append((int(info['sequence']), statvals))
    return [t[1] for t in sorted(temp, key=lambda t: t[0])]


def _json_game_player_stats(game, data):
    """
    Parses the 'home' and 'away' team stats and returns an OrderedDict
    mapping player id to their total game statistics as instances of
    nflgame.player.GamePlayerStats.
    """
    players = OrderedDict()
    for team in ('home', 'away'):
        for category in nflgame.statmap.categories:
            if category not in data[team]['stats']:
                continue
            for pid, raw in data[team]['stats'][category].iteritems():
                stats = {}
                for k, v in raw.iteritems():
                    if k == 'name':
                        continue
                    stats['%s_%s' % (category, k)] = v
                if pid not in players:
                    home = team == 'home'
                    if home:
                        team_name = game.home
                    else:
                        team_name = game.away
                    players[pid] = nflgame.player.GamePlayerStats(pid,
                                                                  raw['name'],
                                                                  home,
                                                                  team_name)
                players[pid]._add_stats(stats)
    return players


def _get_json_data(eid=None, fpath=None):
    """
    Returns the JSON data corresponding to the game represented by eid.

    If the JSON data is already on disk, it is read, decompressed and returned.

    Otherwise, the JSON data is downloaded from the NFL web site. If the data
    doesn't exist yet or there was an error, _get_json_data returns None.

    If eid is None, then the JSON data is read from the file at fpath.
    """
    assert eid is not None or fpath is not None

    if fpath is not None:
        return gzip.open(fpath).read()

    fpath = _jsonf % eid
    if os.access(fpath, os.R_OK):
        return gzip.open(fpath).read()
    try:
        return urllib2.urlopen(_json_base_url % (eid, eid), timeout=5).read()
    except urllib2.HTTPError:
        pass
    except socket.timeout:
        pass
    return None


def _tryint(v):
    """
    Tries to convert v to an integer. If it fails, return 0.
    """
    try:
        return int(v)
    except:
        return 0
