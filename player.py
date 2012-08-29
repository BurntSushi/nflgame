from collections import OrderedDict

class Players (object):
    def __init__(self, gameData):
        self.players = OrderedDict()

    def __get_or_add(self, playerid, name, home):
        if playerid in self.players:
            return self.players[playerid]
        p = Player(playerid)
        self.players[playerid] = p
        return p

    def __len__(self):
        return len(self.players)

    def __getitem__(self, key):
        return self.players[key]

    def __iter__(self):
        return iter(self.players)

    def __reversed__(self):
        return reversed(self.players)

class Player (object):
    def __init__(self, playerid, name, home):
        self.playerid = playerid
        self.name = name
        self.home = home
        self.categories = []

    def __add_stats(self, category, stats):
        assert category not in self.categories, \
                'Cannot add two sets of stats from the same category ' \
                'to the same player "%s"' % self.name
        for stat, val in stats.iteritems():
            self.__dict__['%s_%s' % (category, stat)] = val

