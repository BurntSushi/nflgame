import nflgame

games = nflgame.games(2011, 16)
qbs = nflgame.NoPlayers
for game in games:
    qbs += game.players.kicking()
for qb in qbs:
    print qb, dir(qb)
    break
print dir(qbs)

