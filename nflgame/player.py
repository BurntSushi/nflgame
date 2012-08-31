from collections import OrderedDict
import csv
import functools

categories = ("passing", "rushing", "receiving",
              "fumbles", "kicking", "punting", "kickret", "puntret",
              "defense")
"""
categories is a list of all individual statistical categories reported by
NFL's GameCenter.
"""

_tdfields = ('passing_tds', 'rushing_tds', 'receiving_tds',
             'kickret_tds', 'puntret_tds')


class Players (object):
    """
    Players implements a sequence type and provides a convenient API for
    searching sets of players.
    """

    def __init__(self, iterable):
        """
        Creates a new Players sequence from an iterable where each element
        of the iterable is an instance of the Player class.
        """
        self.__players = iterable

        # This is pretty evil. Basically, we autogenerate a method for each
        # stat category ("passing", "rushing", "receiving", etc...) that
        # returns a generator which filters out any players not in that
        # category.
        for category in categories:
            def gen(category):
                def _gen():
                    for p in self:
                        if p.__dict__[category]:
                            yield p
                return lambda: Players(_gen())
            self.__dict__['_%s' % category] = gen(category)

    def name(self, name):
        """
        Returns a single player whose name equals `name`. If no such player
        can be found, None is returned.

        Note that NFL GameCenter formats their names like "T.Brady" and
        "W.Welker". Thus, `name` should also be in this format.
        """
        for p in self:
            if p.name == name:
                return p
        return None

    def playerid(self, playerid):
        """
        Returns a single player whose NFL GameCenter identifier equals
        `playerid`. This probably isn't too useful, unless you need
        to disambiguate between two players with the name first initial
        and last name.

        If no such player with the given identifier is found, None is
        returned.
        """
        for p in self:
            if p.playerid == playerid:
                return p
        return None

    def touchdowns(self):
        """
        touchdowns is a convenience method for returning a Players
        sequence of all players with at least one touchdown.

        It is essentially a filter on the following fields: passing_tds,
        rushing_tds, receiving_tds, kickret_tds and puntret_tds.
        """
        def gen():
            for p in self:
                for f in _tdfields:
                    if f not in p.__dict__:
                        continue
                    if p.__dict__[f] > 0:
                        yield p
        return Players(gen())

    def filter(self, **kwargs):
        """
        filters the Players sequence based on a set of criteria. Parameter
        names should be equivalent to the properties accessible in instances
        of the Player class.

        For example::

            players.filter(home=True, passing_tds=1, rushing_yds=lambda x: x>0)

        Returns a Players sequence with only players on the home team that
        have a single passing touchdown and more than zero rushing yards.

        If a field specified does not exist for a particular Player, that
        Player is excluded from the result set.

        If a field is set to a value, then only players with fields that equal
        that value are returned.

        If a field is set to a function---which must be a predicate---then
        only players with field values satisfying that function will
        be returned.
        """
        preds = []
        for k, v in kwargs.iteritems():
            def pred(field, value, player):
                if field not in player.__dict__:
                    return False
                if isinstance(value, type(lambda x: x)):
                    return value(player.__dict__[field])
                return player.__dict__[field] == value
            preds.append(functools.partial(pred, k, v))

        def gen():
            for p in self:
                if all([f(p) for f in preds]):
                    yield p
        return Players(gen())

    def passing(self):
        """Returns players that have a "passing" statistical category."""
        return self._passing()

    def rushing(self):
        """Returns players that have a "rushing" statistical category."""
        return self._rushing()

    def receiving(self):
        """Returns players that have a "receiving" statistical category."""
        return self._receiving()

    def fumbles(self):
        """Returns players that have a "fumbles" statistical category."""
        return self._fumbles()

    def kicking(self):
        """Returns players that have a "kicking" statistical category."""
        return self._kicking()

    def punting(self):
        """Returns players that have a "punting" statistical category."""
        return self._punting()

    def kickret(self):
        """Returns players that have a "kickret" statistical category."""
        return self._kickret()

    def puntret(self):
        """Returns players that have a "puntret" statistical category."""
        return self._puntret()

    def defense(self):
        """Returns players that have a "kicking" statistical category."""
        return self._defense()

    def limit(self, n):
        """
        Limit the sequence to N players.
        """
        def gen():
            for i, p in enumerate(self):
                if i >= n:
                    return
                yield p
        return Players(gen())

    def sort(self, field, descending=True):
        """
        sorts the players according to the field specified---where field is
        a property in a Player object. If descending is false, players will
        be sorted in order from least to greatest.

        Note that if field does not exist in any Player being sorted, a
        KeyError will be raised.
        """
        return Players(sorted(self.__players, reverse=descending,
                              key=lambda p: p.__dict__[field]))

    def csv(self, fileName):
        """
        Given a file-name fileName, csv will write the contents of
        the Players sequence to fileName formatted as comma-separated values.
        The resulting file can then be opened directly with programs like
        Excel, Google Docs, Libre Office and Open Office.

        Note that since each player in a Players sequence may have differing
        statistical categories (like a quarterback and a receiver), the
        minimum constraining set of statisical categories is used as the
        header row for the resulting CSV file.
        """
        fields, rows = [], []
        players = list(self)
        for p in players:
            for category, stats in p.all_stats().iteritems():
                for stat in stats:
                    field = '%s_%s' % (category, stat)
                    if field in fields:
                        continue
                    fields.append(field)
        for p in players:
            d = {
                'name': p.name,
                'id': p.playerid,
                'home': p.home and 'yes' or 'no',
            }
            for field in fields:
                if field in p.__dict__:
                    d[field] = p.__dict__[field]
                else:
                    d[field] = ""
            rows.append(d)

        fieldNames = ["name", "id", "home"] + fields
        rows = [{f: f for f in fieldNames}] + rows
        csv.DictWriter(open(fileName, 'w+'), fieldNames).writerows(rows)

    def __add__(self, other):
        """
        Adds two Players sequences by concatenating the generators composing
        each Players sequence.
        """
        if other is None:
            return self

        def gen():
            for p in self:
                yield p
            for p in other:
                yield p
        return Players(gen())

    def __str__(self):
        """Returns a list of player names in the sequence."""
        return '[%s]' % ', '.join([str(p) for p in self])

    def __iter__(self):
        """Make this an iterable sequence."""
        if self.__players is None:
            return iter([])
        if isinstance(self.__players, OrderedDict):
            return self.__players.itervalues()
        return iter(self.__players)

    def __reversed__(self):
        """Satisfy the built in reversed."""
        return reversed(self.__players)


class Player (object):
    """
    Player represents a single player and all of his statistical categories
    for a single game. Every player has 'playerid', 'name' and 'home' fields.
    Additionally, depending upon which statistical categories that player
    was involved in for the game, he'll have properties such as 'passing_tds',
    'rushing_yds', 'defense_int' and 'kicking_fgm'.

    In order to know whether a paricular player belongs to a statical category,
    you may use the filtering methods of a Players sequence or alternatively,
    use the 'passing', 'rushing', 'kicking', etc., boolean members of this
    class.

    You may also inspect whether a player has a certain property by using
    the special __dict__ attribute. For example::

        if 'passing_yds' in player.__dict__:
            # Do something with player.passing_yds
    """
    def __init__(self, playerid, name, home):
        """
        Create a new Player instance with the player id (from NFL.com's
        GameCenter), the player's name (e.g., "T.Brady") and whether the
        player is playing in a home game or not.
        """
        self.playerid = playerid
        self.name = name
        self.home = home
        self.games = 1
        self.__stats = OrderedDict()
        for category in categories:
            self.__dict__[category] = False

    def tds(self):
        """
        Returns the total number of touchdowns credited to this player across
        all statistical categories.
        """
        n = 0
        for f in _tdfields:
            if f in self.__dict__:
                n += self.__dict__[f]
        return n

    def all_stats(self):
        """
        Returns a dict of all stats for the player. Each key is a statistical
        category corresponding to a dict with keys corresponding to each
        statistic and values corresponding to each statistic's value.
        """
        return self.__stats

    def formatted_stats(self):
        """
        Returns a roughly-formatted string of all statistics for this player.
        """
        s = []
        for category in self.__stats.iterkeys():
            for stat, val in self.__stats[category].iteritems():
                s.append('%s_%s: %s' % (category, stat, val))
        return ', '.join(s)

    def _add_stats(self, category, stats):
        assert category not in self.__stats, \
            'Cannot add two sets of stats from the same category ' \
            'to the same player "%s"' % self.name
        self.__dict__[category] = True
        for stat, val in stats.iteritems():
            if stat == "name":
                continue
            self.__dict__['%s_%s' % (category, stat)] = val
            self.__stats.setdefault(category, OrderedDict())[stat] = val

    def __str__(self):
        """
        Simply returns the player's name, e.g., "T.Brady".
        """
        return self.name

    def __add__(self, player):
        """
        Adds two players together. Only two player objects that correspond
        to the same human (i.e., GameCenter identifier) can be added together.

        If two different players are added together, an assertion will
        be raised.

        The effect of adding two player objects simply corresponds to the
        sums of all statistical values.

        Note that as soon as two players have been added, the 'home' property
        becomes undefined.
        """
        assert self.playerid == player.playerid
        new_player = Player(self.playerid, self.name, None)
        new_player.games = self.games + player.games
        stats1 = self.__stats
        stats2 = player.__stats

        # Add stats from self. Piece of cake.
        for category, stats in stats1.iteritems():
            new_player._add_stats(category, stats)

        # Now add stats from player. A little more complicated because
        # we need to *add* them to each value already in new_player's stats.
        for category, stats in stats2.iteritems():
            if not new_player.__dict__[category]:
                assert category not in new_player.__stats
                new_player._add_stats(category, stats)
            else:
                assert category in new_player.__stats
                for k, v in stats.iteritems():
                    if k == 'name':
                        continue
                    new_player.__dict__['%s_%s' % (category, k)] += v
                    new_player.__stats[category][k] += v

        return new_player
