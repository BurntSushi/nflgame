import os
import os.path as path
import gzip
import urllib2

import nflgame.player as player

jsonf = path.join(path.split(__file__)[0], 'gamecenter-json', '%s.json.gz')
json_base_url = "http://www.nfl.com/liveupdate/game-center/%s/%s_gtd.json"

def _get_json(eid):
    fpath = jsonf % eid
    if os.access(fpath, os.R_OK):
        return gzip.open(fpath).read()
    try:
        return urllib2.urlopen(json_base_url % (eid, eid)).read() 
    except urllib2.HTTPError:
        pass
    return None

class Game (object):
    def __init__(self, eid):
        data = _get_json(eid)
        if data is None:
            return
        self.eid = eid
        # self.players = player.Players(data[self.eid]) 
        if self.game_over():
            print >> gzip.open(jsonf % eid, 'w+'), data,

    def game_over(self):
        return True
