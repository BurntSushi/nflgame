from __future__ import division

import json
import os.path

from nflgame import OrderedDict
import nflgame.seq
import nflgame.statmap

_player_json_file = os.path.join(os.path.dirname(__file__), 'players.json')


def _create_players(jsonf=None):
    """
    Creates a dict of Player objects from the players.json file, keyed
    by GSIS ids.
    """
    if jsonf is None:
        jsonf = _player_json_file
    try:
        data = json.loads(open(jsonf).read())
    except IOError:
        return {}

    players = {}
    for playerid in data:
        players[playerid] = Player(data[playerid])
    return players


class Player (object):
    """
    Player instances represent meta information about a single player.
    This information includes name, team, position, status, height,
    weight, college, jersey number, birth date, years, pro, etc.

    Player information is populated from NFL.com profile pages.
    """
    def __init__(self, data):
        self.player_id = data['gsis_id']
        self.gsis_name = data.get('gsis_name', '')
        self.full_name = data.get('full_name', '')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.team = data.get('team', '')
        self.position = data.get('position', '')
        self.profile_id = data.get('profile_id', 0)
        self.profile_url = data.get('profile_url', '')
        self.uniform_number = data.get('number', 0)
        self.birthdate = data.get('birthdate', '')
        self.college = data.get('college', '')
        self.height = data.get('height', '')
        self.weight = data.get('weight', '')
        self.years_pro = data.get('years_pro', 0)
        self.status = data.get('status', '')

        # API backwards compatibility.
        self.gsis_id = self.player_id
        self.playerid = self.player_id
        self.name = self.full_name
        self.number = self.uniform_number

    def stats(self, year, week=None):
        games = nflgame.games(year, week)
        players = list(nflgame.combine(games).filter(playerid=self.playerid))
        if len(players) == 0:
            return GamePlayerStats(self.player_id, self.gsis_name,
                                   None, self.team)
        return players[0]

    def plays(self, year, week=None):
        plays = []
        games = nflgame.games(year, week)
        for g in games:
            plays += filter(lambda p: p.has_player(self.playerid),
                            list(g.drives.plays()))
        return nflgame.seq.GenPlays(plays)

    def __str__(self):
        return '%s (%s, %s)' % (self.name, self.position, self.team)


class PlayerDefense (Player):
    def __init__(self, team):
        self.playerid = None
        self.name = team
        self.team = team
        self.position = 'DEF'

    def stats(self, year, week=None):
        assert False, 'Cannot be called on a defense.'

    def plays(self, year, week=None):
        assert False, 'Cannot be called on a defense.'

    def __str__(self):
        return '%s Defense' % self.team


class PlayerStats (object):
    """
    Player represents a single player and all of his statistical categories.
    Every player has 'playerid', 'name' and 'home' fields.
    Additionally, depending upon which statistical categories that player
    was involved in for the game, he'll have properties such as 'passing_tds',
    'rushing_yds', 'defense_int' and 'kicking_fgm'.

    In order to know whether a paricular player belongs to a statical category,
    you may use the filtering methods of a player sequence or alternatively,
    use the has_cat method with arguments like 'passing', 'rushing', 'kicking',
    etc. (A player sequence in this case would be an instance of
    GenPlayerStats.)

    You may also inspect whether a player has a certain property by using
    the special __dict__ attribute. For example::

        if 'passing_yds' in player.__dict__:
            # Do something with player.passing_yds
    """
    def __init__(self, playerid, name, home, team):
        """
        Create a new Player instance with the player id (from NFL.com's
        GameCenter), the player's name (e.g., "T.Brady") and whether the
        player is playing in a home game or not.
        """
        self.playerid = playerid
        self.name = name
        self.home = home
        self.team = team
        self._stats = OrderedDict()

        self.player = None
        if self.playerid in nflgame.players:
            self.player = nflgame.players[self.playerid]

    def has_cat(self, cat):
        for f in self._stats:
            if f.startswith(cat):
                return True
        return False

    @property
    def guess_position(self):
        """
        Guesses the position of this player based on the statistical
        categories present in this object when player meta is not
        present.

        Note that if this resorts to a guess, then it will be more
        effective on aggregate data rather than data from just a
        single play. (e.g., if a QB runs the ball, and that's the
        only data available, the position returned will be RB.)

        When a position is guessed, only the following positions will
        be returned: QB, RB, WR, DEF, K and P.
        """
        # Look for the player meta first. Duh.
        if self.player is not None:
            return self.player.position

        stats = [
            (self.passing_att, 'QB'),
            (self.rushing_att, 'RB'),
            (self.receiving_tar, 'WR'),
            (self.defense_tkl, 'DEF'),
            (self.defense_ast, 'DEF'),
            (self.kicking_tot, 'K'),
            (self.kicking_fga, 'K'),
            (self.punting_tot, 'P'),
        ]
        return sorted(stats, reverse=True)[0][1]

    @property
    def tds(self):
        """
        Returns the total number of touchdowns credited to this player across
        all statistical categories.
        """
        n = 0
        for f, v in self.__dict__.iteritems():
            if f.endswith('tds'):
                n += v
        return n

    @property
    def twopta(self):
        """
        Returns the total number of two point conversion attempts for
        the passing, rushing and receiving categories.
        """
        return (self.passing_twopta
                + self.rushing_twopta
                + self.receiving_twopta)

    @property
    def twoptm(self):
        """
        Returns the total number of two point conversions for
        the passing, rushing and receiving categories.
        """
        return (self.passing_twoptm
                + self.rushing_twoptm
                + self.receiving_twoptm)

    @property
    def twoptmissed(self):
        """
        Returns the total number of two point conversion failures for
        the passing, rushing and receiving categories.
        """
        return (self.passing_twoptmissed
                + self.rushing_twoptmissed
                + self.receiving_twoptmissed)

    @property
    def stats(self):
        """
        Returns a dict of all stats for the player.
        """
        return self._stats

    def formatted_stats(self):
        """
        Returns a roughly-formatted string of all statistics for this player.
        """
        s = []
        for stat, val in self._stats.iteritems():
            s.append('%s: %s' % (stat, val))
        return ', '.join(s)

    def _add_stats(self, stats):
        for k, v in stats.iteritems():
            self.__dict__[k] = self.__dict__.get(k, 0) + v
            self._stats[k] = self.__dict__[k]

    def _overwrite_stats(self, stats):
        for k, v in stats.iteritems():
            self.__dict__[k] = v
            self._stats[k] = self.__dict__[k]

    def __str__(self):
        """
        Simply returns the player's name, e.g., "T.Brady".
        """
        return self.name

    def __add__(self, other):
        """
        Adds two players together. Only two player objects that correspond
        to the same human (i.e., GameCenter identifier) can be added together.

        If two different players are added together, an assertion will
        be raised.

        The effect of adding two player objects simply corresponds to the
        sums of all statistical values.

        Note that as soon as two players have been added, the 'home' property
        becomes undefined if the two operands have different values of 'home'.
        """
        assert self.playerid == other.playerid
        assert type(self) == type(other)

        if self.home != other.home:
            home = None
        else:
            home = self.home
        new_player = self.__class__(self.playerid, self.name, home, self.team)
        new_player._add_stats(self._stats)
        new_player._add_stats(other._stats)

        return new_player

    def __sub__(self, other):
        assert self.playerid == other.playerid
        assert type(self) == type(other)

        new_player = GamePlayerStats(self.playerid,
                                     self.name, self.home, self.team)
        new_player._add_stats(self._stats)
        for bk, bv in other._stats.iteritems():
            if bk not in new_player._stats:  # stat was taken away? ignore.
                continue

            new_player._stats[bk] -= bv
            if new_player._stats[bk] == 0:
                del new_player._stats[bk]
            else:
                new_player.__dict__[bk] = new_player._stats[bk]

        anydiffs = False
        for k, v in new_player._stats.iteritems():
            if v > 0:
                anydiffs = True
                break
        if not anydiffs:
            return None
        return new_player

    def __getattr__(self, name):
        # If name has one of the categories as a prefix, then return
        # a default value of zero
        for cat in nflgame.statmap.categories:
            if name.startswith(cat):
                return 0
        raise AttributeError

    def passer_rating(self):
        """
        Calculate and return the passer rating using the NFL formula. Passer
        rating is calculated using a player's passing attempts, completions,
        yards, touchdowns, and interceptions. Passer rating in the NFL is on a
        scale from 0 to 158.3.
        """
        l = [((self.passing_cmp / self.passing_att) - .3) * 5]
        l.append(((self.passing_yds / self.passing_att) - 3) * .25)
        l.append((self.tds / self.passing_att) * 20)
        l.append(2.375 - (self.passing_ints / self.passing_att * 25))

        m = []
        for a in l:
            if a < 0:
                a = 0
                m.append(a)
            elif a > 2.375:
                a = 2.375
                m.append(a)
            else:
                m.append(a)

            rating = round((sum(m) / 6) * 100, 1)
        return rating


class GamePlayerStats (PlayerStats):
    def __init__(self, playerid, name, home, team):
        super(GamePlayerStats, self).__init__(playerid, name, home, team)
        self.games = 1

    def __add__(self, other):
        new_player = super(GamePlayerStats, self).__add__(other)
        new_player.games = self.games + other.games
        return new_player


class PlayPlayerStats (PlayerStats):
    pass
