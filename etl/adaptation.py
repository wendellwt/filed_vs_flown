
############################################################################
#                                  adaptation                              #
############################################################################

corners = {

    # note: inside postg.py, corner post is either one navaid or a
    #  tuple of fixes

    'DEN' : { 'ne': 'LANDR', 'se': 'DANDD', 'sw': 'LARKS', 'nw': 'RAMMS', },

    # estimated by looking at chart:
    'ATL' : { 'ne': 'MACEY', 'se': 'SINCA', 'sw': 'SMAWG', 'nw': 'RMG'},

    # guess by looking at chart and from what I remember from my TBFM days:
    'DFW' : { 'ne': 'BYP',  # Bonham vor
              'se': 'CQY',  # Cedar Creek vor
              'sw': 'JEN',  # Glen Rose vor
              'nw': 'UKW'   # Bowie vor
             }
}


# multiple fixes: near_to_corner_post = "0.0833"  # degrees, 5.0 nm  (approx.)
near_to_corner_post = "0.16"  # degrees, 10.0 nm  (approx.)

tracon_radius =  42   # nm circle around airport

# ====================== ARTCC info =====================

parent_artcc = {
    'DEN' : 'ZDV',
    'DFW' : 'ZFW',
    'ATL' : 'ZTL',
}

first_tier = {
    'ZDV' : ("ZLA", "ZLC", "ZMP", "ZKC", "ZAB" ),
    'ZFW' : ("ZAB", "ZKC", "ZME", "ZHU"),
    'ZTL' : ("ZHU", "ZME", "ZID", "ZDC", "ZJX")
}

second_tier = {
    'ZDV' : ("ZOA", "ZSE", "ZAU", "ZID", "ZME", "ZFW")
}
