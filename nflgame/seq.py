import functools
import itertools
import operator

from nflgame import OrderedDict
from nflgame import statmap

_BUILTIN_PREDS = {
    '__lt': operator.lt,
    '__le': operator.le,
    '__ne': operator.ne,
    '__ge': operator.ge,
    '__gt': operator.gt,
}
"""
A dictionary of suffixes to predicates that can be used in Gen.filter.
The suffix corresponds to what to add to the end of a field name to invoke
the predicate it corresponds to. For example, this::

    players.filter(receiving_rec=lambda v: v > 0)

Is equivalent to::

    players.filter(receiving_rec__gt=0)

(Django users should feel right at home.)
"""


class Gen (object):
    """
    Players implements a sequence type and provides a convenient API for
    searching sets of players.
    """

    def __init__(self, iterable):
        """
        Creates a new Players sequence from an iterable where each element
        of the iterable is an instance of the Player class.
        """
        self.__iter = iterable

    def filter(self, **kwargs):
        """
        filters the sequence based on a set of criteria. Parameter
        names should be equivalent to the properties accessible in the items
        of the sequence. For example, where the items are instances of
        the Stats class::

            players.filter(home=True, passing_tds=1, rushing_yds=lambda x: x>0)

        Returns a sequence with only players on the home team that
        have a single passing touchdown and more than zero rushing yards.

        If a field specified does not exist for a particular item, that
        item is excluded from the result set.

        If a field is set to a value, then only items with fields that equal
        that value are returned.

        If a field is set to a function---which must be a predicate---then
        only items with field values satisfying that function will
        be returned.

        Also, special suffixes that begin with '__' may be added to the
        end of a field name to invoke built in predicates.
        For example, this::

            players.filter(receiving_rec=lambda v: v > 0)

        Is equivalent to::

            players.filter(receiving_rec__gt=0)

        Other suffixes includes gt, le, lt, ne, ge, etc.

        (Django users should feel right at home.)
        """
        preds = []
        for k, v in kwargs.iteritems():
            def pred(field, value, item):
                for suffix, p in _BUILTIN_PREDS.iteritems():
                    if field.endswith(suffix):
                        f = field[:field.index(suffix)]
                        if not hasattr(item, f) or getattr(item, f) is None:
                            return False
                        return p(getattr(item, f), value)
                if not hasattr(item, field) or getattr(item, field) is None:
                    return False
                if isinstance(value, type(lambda x: x)):
                    return value(getattr(item, field))
                return getattr(item, field) == value
            preds.append(functools.partial(pred, k, v))

        gen = itertools.ifilter(lambda item: all([f(item) for f in preds]),
                                self)
        return self.__class__(gen)

    def limit(self, n):
        """
        Limit the sequence to N items.
        """
        return self.__class__(itertools.islice(self, n))

    def sort(self, field, descending=True):
        """
        sorts the sequence according to the field specified---where field is
        a property on an item in the sequence. If descending is false, items
        will be sorted in order from least to greatest.

        Note that if field does not exist in any item being sorted, a
        KeyError will be raised.
        """
        def attrget(item):
            return getattr(item, field, 0)

        return self.__class__(sorted(self, reverse=descending, key=attrget))

    def __str__(self):
        """Returns a list of items in the sequence."""
        return '[%s]' % ', '.join([str(item) for item in self])

    def __iter__(self):
        """Make this an iterable sequence."""
        if self.__iter is None:
            return iter([])
        if isinstance(self.__iter, OrderedDict):
            return self.__iter.itervalues()
        return iter(self.__iter)

    def __reversed__(self):
        """Satisfy the built in reversed."""
        return reversed(self.__iter)


class GenDrives (Gen):
    """
    GenDrives implements a sequence type and provides a convenient API
    for searching drives.
    """
    def plays(self):
        """
        Returns all of the plays, in order, belonging to every drive in
        the sequence.
        """
        return GenPlays(itertools.chain(*map(lambda d: d.plays, self)))

    def players(self):
        """
        Returns the combined player stats for every player that participated
        in any of the drives in the sequence.
        """
        return self.plays().players()

    def number(self, n, team=None):
        """
        Gets the Nth drive where the first drive corresponds to n=1. This is
        only useful given a complete collection of drives for an entire game.

        If the team parameter is specified (i.e., team='NE'), then n will
        be interpreted as *that* team's Nth drive.
        """
        assert n > 0
        n -= 1
        if team is None:
            return list(self)[n]
        else:
            i = 0
            for d in self:
                if d.team == team:
                    if i == n:
                        return d
                    i += 1
            assert False, \
                'Could not find drive %d for team %s.' % (n + 1, team)


class GenPlays (Gen):
    """
    GenPlays implements a sequence type and provides a convenient API
    for searching plays.
    """
    def players(self):
        """
        Returns the combined player stats for every play in the sequence.
        """
        players = OrderedDict()
        for play in self:
            for player in play.players:
                if player.playerid not in players:
                    players[player.playerid] = player
                else:
                    players[player.playerid] += player
        return GenPlayerStats(players)


class GenPlayerStats (Gen):
    """
    GenPlayerStats implements a sequence type and provides a convenient API for
    searching sets of player statistics.
    """
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
        `playerid`. This probably isn't too useful, unless you're trying
        to do ID mapping. (Players have different identifiers across NFL.com.)

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
        """
        def gen():
            for p in self:
                for f in p.__dict__:
                    if f.endswith('tds') and p.__dict__[f] > 0:
                        yield p
                        break
        return self.__class__(gen())

    def __filter_category(self, cat):
        return self.__class__(itertools.ifilter(lambda p: p.has_cat(cat),
                                                self))

    def passing(self):
        """Returns players that have a "passing" statistical category."""
        return self.__filter_category('passing')

    def rushing(self):
        """Returns players that have a "rushing" statistical category."""
        return self.__filter_category('rushing')

    def receiving(self):
        """Returns players that have a "receiving" statistical category."""
        return self.__filter_category('receiving')

    def fumbles(self):
        """Returns players that have a "fumbles" statistical category."""
        return self.__filter_category('fumbles')

    def kicking(self):
        """Returns players that have a "kicking" statistical category."""
        return self.__filter_category('kicking')

    def punting(self):
        """Returns players that have a "punting" statistical category."""
        return self.__filter_category('punting')

    def kickret(self):
        """Returns players that have a "kickret" statistical category."""
        return self.__filter_category('kickret')

    def puntret(self):
        """Returns players that have a "puntret" statistical category."""
        return self.__filter_category('puntret')

    def defense(self):
        """Returns players that have a "defense" statistical category."""
        return self.__filter_category('defense')

    def penalty(self):
        """Returns players that have a "penalty" statistical category."""
        return self.__filter_category('penalty')

    def csv(self, fileName, allfields=False):
        """
        Given a file-name fileName, csv will write the contents of
        the Players sequence to fileName formatted as comma-separated values.
        The resulting file can then be opened directly with programs like
        Excel, Google Docs, Libre Office and Open Office.

        Note that since each player in a Players sequence may have differing
        statistical categories (like a quarterback and a receiver), the
        minimum constraining set of statisical categories is used as the
        header row for the resulting CSV file. This behavior can be changed
        by setting 'allfields' to True, which will use every available field
        in the header.
        """
        import csv

        fields, rows = set([]), []
        players = list(self)
        for p in players:
            for field, stat in p.stats.iteritems():
                fields.add(field)
        if allfields:
            for statId, info in statmap.idmap.iteritems():
                for field in info['fields']:
                    fields.add(field)
        fields = sorted(list(fields))

        for p in players:
            d = {
                'name': p.name,
                'id': p.playerid,
                'home': p.home and 'yes' or 'no',
                'team': p.team,
                'pos': 'N/A',
            }
            if p.player is not None:
                d['pos'] = p.player.position

            for field in fields:
                if field in p.__dict__:
                    d[field] = p.__dict__[field]
                else:
                    d[field] = ""
            rows.append(d)

        fieldNames = ["name", "id", "home", "team", "pos"] + fields
        rows = [dict((f, f) for f in fieldNames)] + rows
        csv.DictWriter(open(fileName, 'w+'), fieldNames).writerows(rows)

    def __add__(self, other):
        """
        Adds two sequences of players by combining repeat players and summing
        their statistics.
        """
        players = OrderedDict()
        for p in itertools.chain(self, other):
            if p.playerid not in players:
                players[p.playerid] = p
            else:
                players[p.playerid] += p
        return GenPlayerStats(players)
