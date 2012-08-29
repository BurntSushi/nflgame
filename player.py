from collections import OrderedDict
import csv
import functools

categories = ("passing", "rushing", "receiving",
              "fumbles", "kicking", "punting", "kickret", "puntret",
              "defense")

class Players (object):
    def __init__(self, iterable):
        self.players = iterable

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
            self.__dict__[category] = gen(category)

    def name(self, name):
        for p in self:
            if p.name == name:
                return p
        return None

    def playerid(self, playerid):
        for p in self:
            if p.playerid == playerid:
                return p
        return None

    def touchdowns(self):
        tdfields = ('passing_tds', 'rushing_tds', 'receiving_tds',
                    'kickret_tds', 'puntret_tds')
        def gen():
            for p in self:
                for f in tdfields:
                    if f not in p.__dict__:
                        continue
                    if p.__dict__[f] > 0:
                        yield p
        return Players(gen())

    def filter(self, **kwargs):
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

    def sort(self, field, descending=True):
        return Players(sorted(self.players, reverse=descending,
                       key=lambda p: p.__dict__[field]))

    def csv(self, csvfile):
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
        csv.DictWriter(csvfile, fieldNames).writerows(rows)

    def __add__(self, other):
        if other is None:
            return self
        def gen():
            for p in self:
                yield p
            for p in other:
                yield p
        return Players(gen())

    def __len__(self):
        if self.players is None:
            return 0
        return len(self.players)

    def __str__(self):
        return '[%s]' % ', '.join([str(p) for p in self])

    def __iter__(self):
        if self.players is None:
            return iter([])
        if isinstance(self.players, OrderedDict):
            return self.players.itervalues()
        return iter(self.players)

    def __reversed__(self):
        return reversed(self.players)

class Player (object):
    def __init__(self, playerid, name, home):
        self.playerid = playerid
        self.name = name
        self.home = home
        self.__stats = OrderedDict()
        for category in categories:
            self.__dict__[category] = False

    def all_stats(self):
        return self.__stats

    def formatted_stats(self):
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
        return self.name

