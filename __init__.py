import nflgame.game as game
import nflgame.schedule as schedule

def __search_schedule(year, week=None, home=None, away=None, preseason=False):
    ids = []
    for (y, t, w, h, a), eid in schedule.gameids:
        if y != year:
            continue
        if week is not None and w != week:
            continue
        if home is not None and h != home:
            continue
        if away is not None and a != away:
            continue
        if preseason and t != "PRE":
            continue
        if not preseason and t != "REG":
            continue
        ids.append(eid)
    return ids

def games(year, week=None, home=None, away=None, preseason=False):
    eids = __search_schedule(year, week, home, away, preseason)
    if not eids:
        return None
    return [game.Game(eid) for eid in eids]

def one(year, week, home, away, preseason=False):
    eids = __search_schedule(year, week, home, away, preseason)
    if not eids:
        return None
    assert len(eids) == 1, 'More than one game matches the given criteria.'
    return game.Game(eids[0])

