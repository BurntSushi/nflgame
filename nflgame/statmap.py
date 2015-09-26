"""
The stats module maps statistical category identifiers from NFL.com's
GameCenter JSON feed to a representation of what we believe that statistical
category means. This mapping has been reverse engineered with a lot of help
from reddit users rasherdk and curien.

B{Note}: We now have a data dictionary mapping statistical category id to
a description from nflgsis.com. An original copy is in the root directory
of the nflgame repository (StatIDs.html).

If you think anything here is wrong (or can figure out some of the unknowns),
please let me know by filing an issue here:
https://github.com/BurntSushi/nflgame/issues

For each statistical category identifier, we create a dict of 6 fields
describing that statistical category. The fields are cat, fields, yds, value,
desc and long.

cat specifies which statistical category the particular stat belong in. Only
statistical categories in nflgame.player.categories should be used.

fields specifies the actual statistical field corresponding to the stat. This
will manifest itself as a property on statistical objects via the API. These
fields should correspond to counters; i.e., number of receptions, rushing
attempts, tackles, etc.

yds specifies a field that contains the yardage totals relevant to the stat.
If a stat does not specify yards, this field should be blank (an empty string).

value specifies how much each statistic is worth. This is 1 in every case
except for split sacks.

desc specifies a human readable description for the statistic. It should be
concise and clear. If a statistical category is unknown, then desc should
contain a string like 'Unknown (reason for confusion)'. Valid reasons for
confusion include "data is inconsistent" or "this looks like a duplicate" all
the way to "I have no fucking clue."

long contains a verbatim description from nflgsis.com. Some of the information
clearly references legacy systems, but alas, it is included as it adds to the
context of each statistical category.
"""


def values(category_id, yards):
    """
    Returns a dictionary of field names to statistical values for a
    particular category id defined in idmap.
    """
    assert category_id in idmap, \
        'Category identifier %d is not known.' % category_id
    info = idmap[category_id]
    try:
        yards = int(yards)
    except ValueError:
        yards = 0
    except TypeError:
        # Catch errors if yards is a NoneType
        yards = 0

    vals = {}
    if info['yds']:
        vals[info['yds']] = yards
    for f in info['fields']:
        vals[f] = info.get('value', 1)
    return vals

categories = ("passing", "rushing", "receiving",
              "fumbles", "kicking", "punting", "kickret", "puntret",
              "defense", "penalty")
"""
categories is a list of all statistical categories reported by NFL's
GameCenter.
"""

idmap = {
    2: {
        'cat': 'punting',
        'fields': ['punting_blk'],
        'yds': '',
        'desc': 'Punt blocked (offense)',
        'long': 'Punt was blocked. A blocked punt is a punt that is touched '
                'behind the line of scrimmage, and is recovered, or goes '
                'out of bounds, behind the line of scrimmage. If the '
                'impetus of the punt takes it beyond the line of scrimmage, '
                'it is not a blocked punt.',
    },
    3: {
        'cat': 'team',
        'fields': ['first_down', 'rushing_first_down'],
        'yds': '',
        'desc': '1st down (rushing)',
        'long': 'A first down or TD occurred due to a rush.',
    },
    4: {
        'cat': 'team',
        'fields': ['first_down', 'passing_first_down'],
        'yds': '',
        'desc': '1st down (passing)',
        'long': 'A first down or TD occurred due to a pass.',
    },
    5: {
        'cat': 'team',
        'fields': ['first_down', 'penalty_first_down'],
        'yds': '',
        'desc': '1st down (penalty)',
        'long': 'A first down or TD occurred due to a penalty. A play can '
                'have a first down from a pass or rush and from a penalty.',
    },
    6: {
        'cat': 'team',
        'fields': ['third_down_att', 'third_down_conv'],
        'yds': '',
        'desc': '3rd down attempt converted',
        'long': '3rd down play resulted in a first down or touchdown.',
    },
    7: {
        'cat': 'team',
        'fields': ['third_down_att', 'third_down_failed'],
        'yds': '',
        'desc': '3rd down attempt failed',
        'long': '3rd down play did not result in a first down or touchdown.',
    },
    8: {
        'cat': 'team',
        'fields': ['fourth_down_att', 'fourth_down_conv'],
        'yds': '',
        'desc': '4th down attempt converted',
        'long': '4th down play resulted in a first down or touchdown.',
    },
    9: {
        'cat': 'team',
        'fields': ['fourth_down_att', 'fourth_down_failed'],
        'yds': '',
        'desc': '4th down attempt failed',
        'long': '4th down play did not result in a first down or touchdown.',
    },
    10: {
        'cat': 'rushing',
        'fields': ['rushing_att'],
        'yds': 'rushing_yds',
        'desc': 'Rushing yards',
        'long': 'Rushing yards and credit for a rushing attempt.',
    },
    11: {
        'cat': 'rushing',
        'fields': ['rushing_att', 'rushing_tds'],
        'yds': 'rushing_yds',
        'desc': 'Rushing yards, TD',
        'long': 'Rushing yards and credit for a rushing attempt where the '
                'result of the play was a touchdown.',
    },
    12: {
        'cat': 'rushing',
        'fields': [],
        'yds': 'rushing_yds',
        'desc': 'Rushing yards, No rush',
        'long': 'Rushing yards with no rushing attempt. This will occur when '
                'the initial runner laterals to a second runner, and the '
                'second runner possesses the lateral beyond the line of '
                'scrimmage. Both players get rushing yards, but only the '
                'first player gets a rushing attempt.',
    },
    13: {
        'cat': 'rushing',
        'fields': ['rushing_tds'],
        'yds': 'rushing_yds',
        'desc': 'Rushing yards, TD, No rush',
        'long': 'Rushing yards and no rushing attempt, where the result of '
                'the play was a touchdown. (See id 12.)',
    },
    14: {
        'cat': 'passing',
        'fields': ['passing_att', 'passing_incmp'],
        'yds': '',
        'desc': 'Pass incomplete',
        'long': 'Pass atempt, incomplete.',
    },
    15: {
        'cat': 'passing',
        'fields': ['passing_att', 'passing_cmp'],
        'yds': 'passing_yds',
        'desc': 'Passing yards',
        'long': 'Passing yards and a pass attempt completed.',
    },
    16: {
        'cat': 'passing',
        'fields': ['passing_att', 'passing_cmp', 'passing_tds'],
        'yds': 'passing_yds',
        'desc': 'Passing yards, TD',
        'long': 'Passing yards and a pass attempt completed that resulted in '
                'a touchdown.',
    },
    # 17: Passing Yards, No Pass
    # In SuperStat, this code was used when the initial pass receiver lateraled
    # to a teammate. It was later combined with the "Passing Yards" code to
    # determine the passer's (quarterback's) total passing yardage on the play.
    # This stat is not in use at this time.

    # 18: Passing Yards, YD, No pass
    # Passing yards, no pass attempt, with a result of touchdown. This stat
    # is not in use at this time.
    19: {
        'cat': 'passing',
        'fields': ['passing_att', 'passing_incmp', 'passing_int'],
        'yds': '',
        'desc': 'Interception (by passer)',
        'long': 'Pass attempt that resulted in an interception.',
    },
    20: {
        'cat': 'passing',
        'fields': ['passing_sk'],
        'yds': 'passing_sk_yds',
        'desc': 'Sack yards (offense)',
        'long': 'Number of yards lost on a pass play that resulted in a sack.',
    },
    21: {
        'cat': 'receiving',
        'fields': ['receiving_rec'],
        'yds': 'receiving_yds',
        'desc': 'Pass reception yards',
        'long': 'Pass reception and yards.',
    },
    22: {
        'cat': 'receiving',
        'fields': ['receiving_rec', 'receiving_tds'],
        'yds': 'receiving_yds',
        'desc': 'Pass reception yards, TD',
        'long': 'Same as previous (21), except when the play results in a '
                'touchdown.',
    },
    23: {
        'cat': 'receiving',
        'fields': [],
        'yds': 'receiving_yds',
        'desc': 'Pass reception yards, No reception',
        'long': 'Pass reception yards, no pass reception. This will occur '
                'when the pass receiver laterals to a teammate. The teammate '
                'gets pass reception yards, but no credit for a pass '
                'reception.',
    },
    24: {
        'cat': 'receiving',
        'fields': ['receiving_tds'],
        'yds': 'receiving_yds',
        'desc': 'Pass reception yards, TD, No reception',
        'long': 'Same as previous (23), except when the play results in a '
                'touchdown.',
    },
    25: {
        'cat': 'defense',
        'fields': ['defense_int'],
        'yds': 'defense_int_yds',
        'desc': 'Interception yards',
        'long': 'Interception and return yards.',
    },
    26: {
        'cat': 'defense',
        'fields': ['defense_int', 'defense_tds', 'defense_int_tds'],
        'yds': 'defense_int_yds',
        'desc': 'Interception yards, TD',
        'long': 'Same as previous (25), except when the play results in a '
                'touchdown.',
    },
    27: {
        'cat': 'defense',
        'fields': [],
        'yds': 'defense_int_yds',
        'also': [],
        'desc': 'Interception yards, No interception',
        'long': 'Interception yards, with no credit for an interception. This '
                'will occur when the player who intercepted the pass laterals '
                'to a teammate. The teammate gets interception return yards, '
                'but no credit for a pass interception.',
    },
    28: {
        'cat': 'defense',
        'fields': ['defense_tds', 'defense_int_tds'],
        'yds': 'defense_int_yds',
        'also': [],
        'desc': 'Interception yards, TD, No interception',
        'long': 'Same as previous (27), except when the play results in a '
                'touchdown.',
    },
    29: {
        'cat': 'punting',
        'fields': ['punting_tot'],
        'yds': 'punting_yds',
        'desc': 'Punting yards',
        'long': 'Punt and length of the punt. This stat is not used if '
                'the punt results in a touchback; or the punt is received '
                'in the endzone and run out; or the punt is blocked. This '
                'stat is used exclusively of the PU_EZ, PU_TB and PU_BK '
                'stats.',
    },
    30: {
        'cat': 'punting',
        'fields': ['punting_i20'],
        'yds': '',
        'desc': 'Punt inside 20',
        'long': 'This stat is recorded when the punt return ended inside the '
                'opponent\'s 20 yard line. This is not counted as a punt or '
                'towards punting yards. This stat is used solely to calculate '
                '"inside 20" stats. This stat is used in addition to either a '
                'PU or PU_EZ stat.',
    },
    31: {
        'cat': 'punting',
        'fields': ['punting_tot'],
        'yds': 'punting_yds',
        'desc': 'Punt into endzone',
        'long': 'SuperStat records this stat when the punt is received in '
                'the endzone, and then run out of the endzone. If the play '
                'ends in the endzone for a touchback, the stat is not '
                'recorded. This stat is used exclusively of the PU, PU_TB and '
                'PU_BK stats.',
    },
    32: {
        'cat': 'punting',
        'fields': ['punting_tot', 'punting_touchback'],
        'yds': 'punting_yds',
        'desc': 'Punt with touchback',
        'long': 'Punt and length of the punt when the play results in a '
                'touchback. This stat is used exclusively of the PU, PU_EZ '
                'and PU_BK stats.',
    },
    33: {
        'cat': 'puntret',
        'fields': ['puntret_tot'],
        'yds': 'puntret_yds',
        'desc': 'Punt return yards',
        'long': 'Punt return and yards.',
    },
    34: {
        'cat': 'puntret',
        'fields': ['puntret_tot', 'puntret_tds'],
        'yds': 'puntret_yds',
        'desc': 'Punt return yards, TD',
        'long': 'Same as previous (33), except when the play results in a '
                'touchdown.',
    },
    35: {
        'cat': 'puntret',
        'fields': [],
        'yds': 'puntret_yds',
        'desc': 'Punt return yards, No return',
        'long': 'Punt return yards with no credit for a punt return. This '
                'will occur when the player who received the punt laterals '
                'to a teammate. The teammate gets punt return yards, but no '
                'credit for a return.',
    },
    36: {
        'cat': 'puntret',
        'fields': ['puntret_tds'],
        'yds': 'puntret_yds',
        'desc': 'Punt return yards, TD, No return',
        'long': 'Same as previous (35), except when the play results in a '
                'touchdown.',
    },
    37: {
        'cat': 'team',
        'fields': ['puntret_oob'],
        'yds': '',
        'desc': 'Punt out of bounds',
        'long': 'Punt went out of bounds, no return on the play.',
    },
    38: {
        'cat': 'team',
        'fields': ['puntret_downed'],
        'yds': '',
        'also': [],
        'value': 1,
        'desc': 'Punt downed (no return)',
        'long': 'Punt was downed by kicking team, no return on the play. '
                'The player column this stat will always be NULL.',
    },
    39: {
        'cat': 'puntret',
        'fields': ['puntret_fair'],
        'yds': '',
        'desc': 'Punt - fair catch',
        'long': 'Punt resulted in a fair catch.',
    },
    40: {
        'cat': 'team',
        'fields': ['puntret_touchback'],
        'yds': '',
        'desc': 'Punt - touchback (no return)',
        'long': 'Punt resulted in a touchback. This is the receiving team\'s '
                'version of code 1504/28 (32) above. Both are needed for stat '
                'calculations, especially in season cumulative analysis.',
    },
    41: {
        'cat': 'kicking',
        'fields': ['kicking_tot'],
        'yds': 'kicking_yds',
        'desc': 'Kickoff yards',
        'long': 'Kickoff and length of kick.',
    },
    42: {
        'cat': 'kicking',
        'fields': ['kicking_i20'],
        'yds': '',
        'desc': 'Kickoff inside 20',
        'long': 'Kickoff and length of kick, where return ended inside '
                'opponent\'s 20 yard line. This is not counted as a kick or '
                'towards kicking yards. This code is used solely to calculate '
                '"inside 20" stats. used in addition to a 1701 code.',
    },
    43: {
        'cat': 'kicking',
        'fields': ['kicking_tot'],
        'yds': 'kicking_yds',
        'desc': 'Kickff into endzone',
        'long': 'SuperStat records this stat when the kickoff is received '
                'in the endzone, and then run out of the endzone. If the play '
                'ends in the endzone for a touchback, the stat is not '
                'recorded. Compare to "Punt into endzone."',
    },
    44: {
        'cat': 'kicking',
        'fields': ['kicking_tot', 'kicking_touchback'],
        'yds': 'kicking_yds',
        'desc': 'Kickoff with touchback',
        'long': 'Kickoff resulted in a touchback.',
    },
    45: {
        'cat': 'kickret',
        'fields': ['kickret_ret'],
        'yds': 'kickret_yds',
        'desc': 'Kickoff return yards',
        'long': 'Kickoff return and yards.',
    },
    46: {
        'cat': 'kickret',
        'fields': ['kickret_ret', 'kickret_tds'],
        'yds': 'kickret_yds',
        'desc': 'Kickoff return yards, TD',
        'long': 'Same as previous (45), except when the play results in a '
                'touchdown.',
    },
    47: {
        'cat': 'kickret',
        'fields': [],
        'yds': 'kickret_yds',
        'desc': 'Kickoff return yards, No return',
        'long': 'Kickoff yards with no return. This will occur when the '
                'player who is credited with the return laterals to a '
                'teammate. The teammate gets kickoff return yards, but no '
                'credit for a kickoff return.',
    },
    48: {
        'cat': 'kickret',
        'fields': ['kickret_tds'],
        'yds': 'kickret_yds',
        'desc': 'Kickoff return yards, TD, No return',
        'long': 'Same as previous (47), except when the play results in a '
                'touchdown.',
    },
    49: {
        'cat': 'team',
        'fields': ['kickret_oob'],
        'yds': '',
        'desc': 'Kickoff out of bounds',
        'long': 'Kicked ball went out of bounds.',
    },
    50: {
        'cat': 'kickret',
        'fields': ['kickret_fair'],
        'yds': '',
        'desc': 'Kickoff - fair catch',
        'long': 'Kick resulted in a fair catch (no return).',
    },
    51: {
        'cat': 'team',
        'fields': ['kickret_touchback'],
        'yds': '',
        'desc': 'Kickoff - touchback',
        'long': 'Kick resulted in a touchback. A touchback implies that '
                'there is no return.',
    },
    52: {
        'cat': 'fumbles',
        'fields': ['fumbles_tot', 'fumbles_forced'],
        'yds': '',
        'desc': 'Fumble - forced',
        'long': 'Player fumbled the ball, fumble was forced by another '
                'player.',
    },
    53: {
        'cat': 'fumbles',
        'fields': ['fumbles_tot', 'fumbles_notforced'],
        'yds': '',
        'desc': 'Fumble - not forced',
        'long': 'Player fumbled the ball, fumble was not forced by another '
                'player.',
    },
    54: {
        'cat': 'fumbles',
        'fields': ['fumbles_oob'],
        'yds': '',
        'desc': 'Fumble - out of bounds',
        'long': 'Player fumbled the ball, and the ball went out of bounds.',
    },
    55: {
        'cat': 'fumbles',
        'fields': ['fumbles_rec'],
        'yds': 'fumbles_rec_yds',
        'desc': 'Own recovery yards',
        'long': 'Yardage gained/lost by a player after he recovered a fumble '
                'by his own team.',
    },
    56: {
        'cat': 'fumbles',
        'fields': ['fumbles_rec', 'fumbles_rec_tds'],
        'yds': 'fumbles_rec_yds',
        'desc': 'Own recovery yards, TD',
        'long': 'Same as previous (55), except when the play results in a '
                'touchdown.',
    },
    57: {
        'cat': 'fumbles',
        'fields': [],
        'yds': 'fumbles_rec_yds',
        'desc': 'Own recovery yards, No recovery',
        'long': 'If a player recovered a fumble by his own team, then '
                'lateraled to a teammate, the yardage gained/lost by teammate '
                'would be recorded with this stat.',
    },
    58: {
        'cat': 'fumbles',
        'fields': ['fumbles_rec_tds'],
        'yds': 'fumbles_rec_yds',
        'desc': 'Own recovery yards, TD, No recovery',
        'long': 'Same as previous (57), except when the play results in a '
                'touchdown.',
    },
    59: {
        'cat': 'defense',
        'fields': ['defense_frec'],
        'yds': 'defense_frec_yds',
        'desc': 'Opponent recovery yards',
        'long': 'Yardage gained/lost by a player after he recovered a fumble '
                'by the opposing team.',
    },
    60: {
        'cat': 'defense',
        'fields': ['defense_frec', 'defense_tds', 'defense_frec_tds'],
        'yds': 'defense_frec_yds',
        'desc': 'Opponent recovery yards, TD',
        'long': 'Same as previous (59), except when the play results in a '
                'touchdown.',
    },
    61: {
        'cat': 'defense',
        'fields': [],
        'yds': 'defense_frec_yds',
        'desc': 'Opponent recovery yards, No recovery',
        'long': 'If a player recovered a fumble by the opposing team, then '
                'lateraled to a teammate, the yardage gained/lost by the '
                'teammate would be recorded with this stat.',
    },
    62: {
        'cat': 'defense',
        'fields': ['defense_tds', 'defense_frec_tds'],
        'yds': 'defense_frec_yds',
        'desc': 'Opponent recovery yards, TD, No recovery',
        'long': 'Same as previous, except when the play results in a '
                'touchdown.',
    },
    63: {
        'cat': 'defense',
        'fields': [],
        'yds': 'defense_misc_yds',
        'desc': 'Miscellaneous yards',
        'long': 'This is sort of a catch-all for yardage that doesn\'t '
                'fall into any other category. According to Elias, it does '
                'not include loose ball yardage. Examples are yardage on '
                'missed field goal, blocked punt. This stat is not used '
                'to "balance the books."',
    },
    64: {
        'cat': 'defense',
        'fields': ['defense_tds', 'defense_misc_tds'],
        'yds': 'defense_misc_yds',
        'desc': 'Miscellaneous yards, TD',
        'long': 'Same as previous (63), except when the play results in a '
                'touchdown.',
    },
    68: {
        'cat': 'team',
        'fields': ['timeout'],
        'yds': '',
        'desc': 'Timeout',
        'long': 'Team took a time out.',
    },
    69: {
        'cat': 'kicking',
        'fields': ['kicking_fga', 'kicking_fgmissed'],
        'yds': 'kicking_fgmissed_yds',
        'desc': 'Field goal missed yards',
        'long': 'The length of a missed field goal.',
    },
    70: {
        'cat': 'kicking',
        'fields': ['kicking_fga', 'kicking_fgm'],
        'yds': 'kicking_fgm_yds',
        'desc': 'Field goal yards',
        'long': 'The length of a successful field goal.',
    },
    71: {
        'cat': 'kicking',
        'fields': ['kicking_fga', 'kicking_fgmissed', 'kicking_fgb'],
        'yds': 'kicking_fgmissed_yds',
        'desc': 'Field goal blocked (offense)',
        'long': 'The length of an attempted field goal that was blocked. '
                'Unlike a punt, a field goal is statistically blocked even '
                'if the ball does go beyond the line of scrimmage.',
    },
    72: {
        'cat': 'kicking',
        'fields': ['kicking_xpa', 'kicking_xpmade'],
        'yds': '',
        'desc': 'Extra point - good',
        'long': 'Extra point good. SuperStat uses one code for both '
                'successful and unsuccessful extra points. I think it might '
                'be better to use 2 codes.',
    },
    73: {
        'cat': 'kicking',
        'fields': ['kicking_xpa', 'kicking_xpmissed'],
        'yds': '',
        'desc': 'Extra point - failed',
        'long': 'Extra point failed.',
    },
    74: {
        'cat': 'kicking',
        'fields': ['kicking_xpa', 'kicking_xpmissed', 'kicking_xpb'],
        'yds': '',
        'desc': 'Extra point - blocked',
        'long': 'Extra point blocked. Exclusive of the extra point failed '
                'stat.'
    },
    75: {
        'cat': 'rushing',
        'fields': ['rushing_twopta', 'rushing_twoptm'],
        'yds': '',
        'desc': '2 point rush - good',
        'long': 'Extra points by run good (old version has 0/1 in yards '
                'for failed/good).',
    },
    76: {
        'cat': 'rushing',
        'fields': ['rushing_twopta', 'rushing_twoptmissed'],
        'yds': '',
        'desc': '2 point rush - failed',
        'long': '',
    },
    77: {
        'cat': 'passing',
        'fields': ['passing_twopta', 'passing_twoptm'],
        'yds': '',
        'desc': '2 point pass - good',
        'long': 'Extra points by pass good (old version has 0/1 in yards '
                'for failed/good).',
    },
    78: {
        'cat': 'passing',
        'fields': ['passing_twopta', 'passing_twoptmissed'],
        'yds': '',
        'desc': '2 point pass - failed',
        'long': 'Extra point by pass failed.',
    },
    79: {
        'cat': 'defense',
        'fields': ['defense_tkl'],
        'yds': '',
        'desc': 'Solo tackle',
        'long': 'Tackle with no assists. Note: There are no official '
                'defensive statistics except for sacks.',
    },
    80: {
        'cat': 'defense',
        'fields': ['defense_tkl', 'defense_tkl_primary'],
        'yds': '',
        'desc': 'Assisted tackle',
        'long': 'Tackle with one or more assists.',
    },
    # 81: 1/2 tackle
    # Tackle split equally between two players. This stat is not in use at
    # this time.
    82: {
        'cat': 'defense',
        'fields': ['defense_ast'],
        'yds': '',
        'desc': 'Tackle assist',
        'long': 'Assist to a tackle.',
    },
    83: {
        'cat': 'defense',
        'fields': ['defense_sk'],
        'yds': 'defense_sk_yds',
        'value': 1.0,
        'desc': 'Sack yards (defense)',
        'long': 'Unassisted sack.',
    },
    84: {
        'cat': 'defense',
        'fields': ['defense_sk'],
        'yds': 'defense_sk_yds',
        'value': 0.5,
        'desc': '1/2 sack yards (defense)',
        'long': 'Sack split equally between two players.',
    },
    85: {
        'cat': 'defense',
        'fields': ['defense_pass_def'],
        'yds': '',
        'desc': 'Pass defensed',
        'long': 'Incomplete pass was due primarily to the player\'s action.',
    },
    86: {
        'cat': 'defense',
        'fields': ['defense_puntblk'],
        'yds': '',
        'desc': 'Punt blocked (defense)',
        'long': 'Player blocked a punt.',
    },
    87: {
        'cat': 'defense',
        'fields': ['defense_xpblk'],
        'yds': '',
        'desc': 'Extra point blocked (defense)',
        'long': 'Player blocked the extra point.',
    },
    88: {
        'cat': 'defense',
        'fields': ['defense_fgblk'],
        'yds': '',
        'desc': 'Field goal blocked (defense)',
        'long': '',
    },
    89: {
        'cat': 'defense',
        'fields': ['defense_safe'],
        'yds': '',
        'desc': 'Safety (defense)',
        'long': 'Tackle that resulted in a safety. This is in addition to '
                'a tackle.',
    },
    # 90: 1/2 safety (defense)
    # This stat was used by SuperStat when a 1/2 tackle resulted in a safety.
    # This stat is not in use at this time.
    91: {
        'cat': 'defense',
        'fields': ['defense_ffum'],
        'yds': '',
        'desc': 'Forced fumble (defense)',
        'long': 'Player forced a fumble.',
    },
    93: {
        'cat': 'penalty',
        'fields': ['penalty'],
        'yds': 'penalty_yds',
        'desc': 'Penalty',
        'long': '',
    },
    95: {
        'cat': 'team',
        'fields': ['rushing_loss'],
        'yds': 'rushing_loss_yds',
        'desc': 'Tackled for a loss',
        'long': 'Tackled for a loss (TFL) is an offensive stat. A team is '
                'charged with a TFL if its rush ends behind the line of '
                'scrimmage, and at least one defensive player is credited '
                'with ending the rush with a tackle, or tackle assist. The '
                'stat will contain yardage.',
    },
    # I'm not sure how to classify these...

    # 96: Extra point - safety
    # If there is a fumble on an extra point attempt, and the loose ball goes
    # into the endzone from impetus provided by the defensive team, and
    # becomes dead in the endzone, the offense is awarded 1 point.

    # 99: 2  point rush - safety
    # See "Extra point - safety".

    # 100: 2  point pass - safety
    # See "Extra point - safety".
    102: {
        'cat': 'team',
        'fields': ['kicking_downed'],
        'yds': '',
        'desc': 'Kickoff - kick downed',
        'long': 'SuperStat didn\'t have this code. A kickoff is "downed" when '
                'touched by an offensive player within the 10 yard free zone, '
                'and the ball is awarded to the receivers at the spot of the '
                'touch.',
    },
    103: {
        'cat': 'passing',
        'fields': [],
        'yds': 'passing_sk_yds',
        'desc': 'Sack yards (offense), No sack',
        'long': 'This stat will be used when the passer fumbles, then '
                'recovers, then laterals. The receiver of the lateral gets '
                'sack yardage but no sack.',
    },
    104: {
        'cat': 'receiving',
        'fields': ['receiving_twopta', 'receiving_twoptm'],
        'yds': '',
        'desc': '2 point pass reception - good',
        'long': '',
    },
    105: {
        'cat': 'receiving',
        'fields': ['receiving_twopta', 'receiving_twoptmissed'],
        'yds': '',
        'desc': '2 point pass reception - failed',
        'long': '',
    },
    106: {
        'cat': 'fumbles',
        'fields': ['fumbles_lost'],
        'yds': '',
        'desc': 'Fumble - lost',
        'long': '',
    },
    107: {
        'cat': 'kicking',
        'fields': ['kicking_rec'],
        'yds': '',
        'desc': 'Own kickoff recovery',
        'long': 'Direct recovery of own kickoff, whether or not the kickoff '
                'is onside',
    },
    108: {
        'cat': 'kicking',
        'fields': ['kicking_rec', 'kicking_rec_tds'],
        'yds': '',
        'desc': 'Own kickoff recovery, TD',
        'long': 'Direct recovery in endzone of own kickoff, whether or not '
                'the kickoff is onside.',
    },
    110: {
        'cat': 'defense',
        'fields': ['defense_qbhit'],
        'yds': '',
        'desc': 'Quarterback hit',
        'long': 'Player knocked the quarterback to the ground, quarterback '
                'was not the ball carrier. Not available for games before '
                '2006 season.',
    },
    111: {
        'cat': 'passing',
        'fields': [],
        'yds': 'passing_cmp_air_yds',
        'desc': 'Pass length, completion',
        'long': 'Length of the pass, not including the yards gained by the '
                'receiver after the catch. Unofficial stat. Not available for '
                'games before 2006 season.',
    },
    112: {
        'cat': 'passing',
        'fields': [],
        'yds': 'passing_incmp_air_yds',
        'desc': 'Pass length, No completion',
        'long': 'Length of the pass, if it would have been a completion.'
                'Unofficial stat. Not available for games before 2006 season.',
    },
    113: {
        'cat': 'receiving',
        'fields': [],
        'yds': 'receiving_yac_yds',
        'desc': 'Yardage gained after the catch',
        'long': 'Yardage from where the ball was caught until the player\'s '
                'action was over. Unofficial stat. Not available for games '
                'before 2006 season.',
    },
    115: {
        'cat': 'receiving',
        'fields': ['receiving_tar'],
        'yds': '',
        'desc': 'Pass target',
        'long': 'Player was the target of a pass attempt. Unofficial stat. '
                'Not available for games before 2009 season.',
    },
    120: {
        'cat': 'defense',
        'fields': ['defense_tkl_loss'],
        'yds': '',
        'desc': 'Tackle for a loss',
        'long': 'Player tackled the runner behind the line of scrimmage. '
                'Play must have ended, player must have received a tackle '
                'stat, has to be an offensive player tackled. Unofficial '
                'stat. Not available for games before 2008 season.',
    },
    # 201, 211, 212 and 213 are for NFL Europe.
    301: {
        'cat': 'team',
        'fields': ['xp_aborted'],
        'yds': '',
        'desc': 'Extra point - aborted',
        'long': '',
    },
    402: {
        'cat': 'defense',
        'fields': [],
        'yds': 'defense_tkl_loss_yds',
        'desc': 'Tackle for a loss yards',
        'long': '',
    },
    410: {
        'cat': 'kicking',
        'fields': [],
        'yds': 'kicking_all_yds',
        'desc': 'Kickoff and length of kick',
        'long': 'Kickoff and length of kick. Includes end zone yards '
                'for all kicks into the end zone, including kickoffs '
                'ending in a touchback.',
    },
}
