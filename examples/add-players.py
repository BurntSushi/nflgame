import nflgame

games = nflgame.games(2011)
players = nflgame.combine(games)

for p in players.passing().sort("passing_yds").limit(35):
    print p, p.passing_yds, p.passing_cmp, p.passing_att, p.passing_tds

