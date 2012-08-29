import os
import os.path
import urllib2

jsonf = os.path.join(os.path.split(__file__)[0], 'gamecenter-json', '%s.json')
json_base_url = "http://www.nfl.com/liveupdate/game-center/%s/%s_gtd.json"

def _get_json(eid):
    fpath = jsonf % eid
    if os.access(fpath, os.R_OK):
        return open(fpath).read()
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
        if self.game_over():
            print >> open(jsonf % eid, 'w+'), data,

    def game_over(self):
        return True
