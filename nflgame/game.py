from collections import OrderedDict
import os
import os.path as path
import gzip
import json
import urllib2

import nflgame.player as player

_jsonf = path.join(path.split(__file__)[0], 'gamecenter-json', '%s.json.gz')
_json_base_url = "http://www.nfl.com/liveupdate/game-center/%s/%s_gtd.json"

class Game (object):
    """
    Game represents a single pre- or regular-season game. It provides a window
    into the statistics of every player that played into the game, along with
    the winner of the game, the score and a list of all the scoring plays.
    """

    eid = 0
    """The identifier of the player used by NFL's GameCenter live update."""

    players = None
    """A sequence of all players that can be searched, sorted and filtered."""

    data = None
    """The raw decoded JSON."""

    home = ""
    """Abbreviation for the home team."""

    away = ""
    """Abbreviation for the away team."""

    score_home_final = 0
    """Final score for the home team."""

    score_away_final = 0
    """Final score for the away team."""

    winner = ""
    """Abbreviated team name of the winner of the game."""

    scores = []
    """A list of scoring plays in the order in which they occurred."""

    def __new__(cls, eid):
        # If we can't get a valid JSON data, exit out and return None.
        rawData = _get_json_data(eid)
        if rawData is None or rawData.strip() == '{}':
            return None
        game = object.__new__(cls, eid)
        game.rawData = rawData
        return game

    def __init__(self, eid):
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

        self.eid = eid
        self.data = json.loads(self.rawData)[self.eid]

        self.__load_all_players(self.data)
        self.players = player.Players(self.__players)

        fpath = _jsonf % eid
        if self.game_over() and not os.access(fpath, os.R_OK):
            print >> gzip.open(fpath, 'w+'), self.rawData,

        # Load up some simple static values.
        self.home = self.data['home']['abbr']
        self.away = self.data['away']['abbr']
        self.score_home_final = int(self.data['home']['score']['T'])
        self.score_away_final = int(self.data['away']['score']['T'])
        for q in (1, 2, 3, 4, 5):
            for team in ('home', 'away'):
                score = self.data[team]['score'][str(q)]
                self.__dict__['score_%s_q%d' % (team, q)] = int(score)
        if self.score_home_final > self.score_away_final:
            self.winner = self.home
        elif self.score_away_final > self.score_home_final:
            self.winner = self.away
        else:
            self.winner = 'TIE'

        # Load the scoring summary into a simple list of strings.
        for k in sorted(map(int, self.data['scrsummary'])):
            play = self.data['scrsummary'][str(k)]
            s = '%s - Q%d - %s - %s' \
                % (play['team'], play['qtr'], play['type'], play['desc'])
            self.scores.append(s)

    def game_over(self):
        """game_over returns true if the game is no longer being played."""
        return self.data['qtr'] == 'Final'

    def __load_all_players(self, gameData):
        self.__players = OrderedDict()
        for team in ("home", "away"):
            for category in player.categories:
                if category not in gameData[team]["stats"]:
                    continue
                catplayers = gameData[team]["stats"][category]
                for playerid, stats in catplayers.iteritems():
                    p = self.__get_or_add_player(playerid, stats["name"],
                                                 team == "home")
                    p._add_stats(category, stats)

    def __get_or_add_player(self, playerid, name, home):
        if playerid in self.__players:
            return self.__players[playerid]
        p = player.Player(playerid, name, home)
        self.__players[playerid] = p
        return p

def _get_json_data(eid):
    """
    Returns the JSON data corresponding to the game represented by eid.

    If the JSON data is already on disk, it is read, decompressed and returned.

    Otherwise, the JSON data is downloaded from the NFL web site. If the data
    doesn't exist yet or there was an error, _get_json_data returns None.
    """
    fpath = _jsonf % eid
    if os.access(fpath, os.R_OK):
        return gzip.open(fpath).read()
    try:
        return urllib2.urlopen(_json_base_url % (eid, eid)).read() 
    except urllib2.HTTPError:
        pass
    return None
