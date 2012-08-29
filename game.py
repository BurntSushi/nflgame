from collections import OrderedDict
import os
import os.path as path
import gzip
import json
import urllib2

import nflgame.player as player

jsonf = path.join(path.split(__file__)[0], 'gamecenter-json', '%s.json.gz')
json_base_url = "http://www.nfl.com/liveupdate/game-center/%s/%s_gtd.json"

def _get_json_data(eid):
    fpath = jsonf % eid
    if os.access(fpath, os.R_OK):
        return gzip.open(fpath).read()
    try:
        return urllib2.urlopen(json_base_url % (eid, eid)).read() 
    except urllib2.HTTPError:
        pass
    return None

class Game (object):
    """A sequence of all players that can be searched, sorted and filtered."""
    players = None

    def __init__(self, eid):
        rawData = _get_json_data(eid)
        if rawData is None:
            return

        self.eid = eid
        self.data = json.loads(rawData)[self.eid]

        self.__load_all_players(self.data)
        self.players = player.Players(self.__players)

        fpath = jsonf % eid
        if self.game_over() and not os.access(fpath, os.R_OK):
            print >> gzip.open(fpath, 'w+'), rawData,

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
        self.scores = []
        for k in sorted(map(int, self.data['scrsummary'])):
            play = self.data['scrsummary'][str(k)]
            s = '%s - Q%d - %s - %s' \
                % (play['team'], play['qtr'], play['type'], play['desc'])
            self.scores.append(s)

    def game_over(self):
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
