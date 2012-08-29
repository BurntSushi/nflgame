import nflgame

games = nflgame.games(2011, 16)
qbs = nflgame.NoPlayers
for game in games:
    qbs += game.players.passing()
best = qbs.sort("passing_att")
for qb in best:
    print qb, qb.passing_att
best.csv(open('test.csv', 'w+'))
best.csv(open('test.csv', 'w+'))

