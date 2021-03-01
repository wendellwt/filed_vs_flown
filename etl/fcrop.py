
# EXPERIMENT: collect all shape cropping routines into one file

import pandas as pd
import shapefile
from shapely import wkb
import fpostg   # Q: does this make MULTIPLE CONNECTIONS (for each import?)
from shapely.geometry import shape, Point, LineString, Polygon

# -----------------------  read shapefile of artcc and tracon

#           -     within                 ;  upto
# parent    - inters of center minus trc ; diff with center
# any tier1 - inters of that center      ; diff with U of cntr + all tier 1
# any tier2 - inters of that center      ; diff with U of cntr + all tier 1 + 2

# full      - (*)difference with tracon  ; na

# ---- globals:

within_shp = None
tracon_shp = None
upto_shp   = None

def read_masking_shapes(ctr, tier, tracon_shapefile, all_artccs, verbose=False):
    global within_shp, tracon_shp, upto_shp

    # ---- There's always a tracon involved

    # ---- 1a. read shapefile using with PyShp

    tracon_esri = shapefile.Reader(tracon_shapefile)
    tracon_feature = tracon_esri.shapeRecords()[0]
    tracon_geom = tracon_feature.shape.__geo_interface__
    tracon_shp = shape(tracon_geom)

    if ctr == 'ZZZ':
        within_shp = None   # just to make sure they aren't used...
        upto_shp   = None   # just to make sure they aren't used...
        return

    # ---- 1. within shape is center minus tracon (always?)

    ctr_wkb = fpostg.get_shape_of_ctr(ctr, verbose)

    center_shape = wkb.loads(ctr_wkb[0][0], hex=True)

    # and have _shapely_ take the difference:
    # if center is parent, then remove tracon,
    # if center is not parent, then this shouldn't matter (right?)

    within_shp = center_shape.difference(tracon_shp)

    # ---- 2. get upto shape

    # 2a. if parent, then shape is just the parent center itself

    if tier == 'parent':

        upto_shp = center_shape

    if tier == '1sttier':

        upto_shp = Polygon()

        for c in all_artccs:

            if c[1] == 'parent' or c[1] == '1sttier':

                ctr_wkb = fpostg.get_shape_of_ctr(c[0], verbose)
                ctr_shape = wkb.loads(ctr_wkb[0][0], hex=True)

                upto_shp = upto_shp.union(ctr_shape)

    if tier == '2ndtier':

        upto_shp = Polygon()

        for c in all_artccs:

            # pretty much any currently listed...
            if c[1] == 'parent' or c[1] == '1sttier' or c[1] == '2ndtier':

                ctr_wkb = fpostg.get_shape_of_ctr(c[0], verbose)
                ctr_shape = wkb.loads(ctr_wkb[0][0], hex=True)

                upto_shp = upto_shp.union(ctr_shape)

# =========================================================================

# ==== ==== ==== each path INTERSECTED with artcc shape

# NOTE: if artcc is real, these are the WITHIN,
#       if artcc is zzz, these are the FULL (but still without the tracon)

def get_all_withins(ctr_df, ctr):

    for (wp, p) in ( ('scheduled_within_path'  , 'scheduled_path'   ),
                     ('first_filed_within_path', 'first_filed_path' ),
                     ('last_filed_within_path' , 'last_filed_path'  ),
                     ('flown_within_path'      , 'flown_path'       ) ):

        ctr_df[wp] = ctr_df[p].apply(lambda p: do_w_intersect(p, ctr))

    for (wd, wp) in ( ('scheduled_within_dist'  , 'scheduled_within_path'  ),
                      ('first_filed_within_dist', 'first_filed_within_path'),
                      ('last_filed_within_dist' , 'last_filed_within_path' ),
                      ('flown_within_dist'      , 'flown_within_path'      ) ):

        ctr_df[wd] = ctr_df[wp].apply(lambda p: gc_length(p))

    return(ctr_df)

# =========================================================================

# ==== ==== ==== (cp wants these) each path DIFFERENCE with tracon

def get_all_uptos(ctr_df):

    for (up, p) in ( ('scheduled_upto_path'  , 'scheduled_path'   ),
                     ('first_filed_upto_path', 'first_filed_path' ),
                     ('last_filed_upto_path' , 'last_filed_path'  ),
                     ('flown_upto_path'      , 'flown_path'       ) ):

        ctr_df[up] = ctr_df[p].apply(lambda p: do_u_difference(p))

    for (ud, up) in ( ('scheduled_upto_dist'  , 'scheduled_upto_path'  ),
                      ('first_filed_upto_dist', 'first_filed_upto_path'),
                      ('last_filed_upto_dist' , 'last_filed_upto_path' ),
                      ('flown_upto_dist'      , 'flown_upto_path'      ) ):

        ctr_df[ud] = ctr_df[up].apply(lambda p: gc_length(p))

    return(ctr_df)

# =========================================================================

def fake_all_uptos(ctr_df):

    ctr_df['scheduled_upto_path'  ] = LineString()
    ctr_df['first_filed_upto_path'] = LineString()
    ctr_df['last_filed_upto_path' ] = LineString()
    ctr_df['flown_upto_path'      ] = LineString()

    ctr_df['scheduled_upto_dist'  ] = 0
    ctr_df['first_filed_upto_dist'] = 0
    ctr_df['last_filed_upto_dist' ] = 0
    ctr_df['flown_upto_dist'      ] = 0

    return(ctr_df)

# ========================================================================

# DUH!!! this gets the ENTIRE DISTANCE OUTSIDE of the artcc!!!

def do_u_difference(path_ls):

    int_path = path_ls.difference(upto_shp)
    return int_path

# ++++++++++++++++++++++++++++++++++++++++++++

def do_f_difference(path_ls):

    int_path = path_ls.difference(tracon_shp)
    return int_path

# ++++++++++++++++++++++++++++++++++++++++++++

# mon am: special check -- if ctr == ZZZ then just take tracon diff,
#                                        else do real intersection

def do_w_intersect(path_ls, ctr):

    if ctr != 'ZZZ':
        int_path = path_ls.intersection(within_shp)
    else:
        int_path = path_ls.difference(tracon_shp)
    return int_path

# =========================================================================

from geopy import distance

# ---- ---- calc G.C. DISTANCE (length) of one linestring (or multilinestring)

def gc_length(ls_path):

    if ls_path.is_empty:
        return(0)

    if ls_path.geom_type=="LineString":

        return(help_gc_length_one_segment(ls_path))

    else:
        if ls_path.geom_type=="MultiLineString":
            sum=0
            for each_path in ls_path:

                sum += help_gc_length_one_segment(each_path)

            return(sum)

        else:
            print("HELP: don't know how to measure distance of:", ls_path.geom_type)
            return(0)

    return(0)  # ???

# sometimes there is:
# GEOMETRYCOLLECTION (POINT (-94.05 36.75), LINESTRING (-86.64 34.13, ...

# =========================================================================

def help_gc_length_one_segment(ls_path):

    if ls_path.is_empty:
        return(0)

    if ls_path.geom_type=="MultiLineString":
        print("HELP: MultiLineString")
        return(99)

    lon_lat = list(ls_path.coords)

    # If you pass coordinates as positional args, please make sure that the
    # order is (latitude, longitude) or (y, x) in Cartesian terms.

    # swap each pair of elements to get right order for geopy's distance()
    lat_lon = [(item[1], item[0]) for item in lon_lat]

    segments = [(lat_lon[k], lat_lon[k + 1]) for k in range(len(lat_lon)-1)]

    dsegs = [distance.distance(seg[0], seg[1]).nautical for seg in segments]

    return(sum(dsegs))

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def get_at_entry_sch_paths(all_scheds_df, flw_pts_df, center_shp):

    # ---- first, get all TZ within the artcc:

    tz_within = flw_pts_df.loc[flw_pts_df['position'].intersects(center_shp)]

    # ---- second, get the first POSIT_TIME of each FID

    first_tz_within = tz_within.sort_values("POSIT_TIME") \
                               .groupby("FID", as_index=False).last()

    # ---- third, match those FIDs with the original SCHED ones

    sched_with_tz_df = pd.merge(first_tz_within, all_scheds_df,
                                on='FID', how='inner')

    # ---- fourth, keep just the rows where orig_time <= first tz time

    scheds_outside_df = sched_with_tz_df.loc[
              sched_with_tz_df['ORIG_TIME'] < sched_with_tz_df['POSIT_TIME'] ]

    # and get the last (largest) times of those

    at_entry_df = scheds_outside_df.sort_values("ORIG_TIME")  \
                                   .groupby("FID", as_index=False).first()

    return(at_entry_df)

# ==========================================================================

# note: artcc is a real one (not ZZZ), so shapes are properly formed

def get_before_entry_single_artcc(ctr_df, all_scheds_df, flown_pts_df):

    # get df of rows from sched_df having orig_time last one before artcc entry

    at_entry_df = get_at_entry_sch_paths(all_scheds_df, flown_pts_df,
                                         upto_shp)

    # and make a linestring of those waypoints, and get dist

    at_entry_df['at_entry_path'] = at_entry_df.apply( lambda row:
                                    form_linestring(row), axis=1)

    for (wp, p) in ( ('at_entry_within_path', 'at_entry_path'), ):

        at_entry_df[wp] = at_entry_df[p].apply(
                                         ambda p: do_w_intersect(p, 'NOT_ZZZ'))

    for (wd, wp) in ( ('at_entry_within_dist', 'at_entry_within_path'), ):

        at_entry_df[wd] = at_entry_df[wp].apply(lambda p: gc_length(p))

    both_df = pd.merge(ctr_df, at_entry_df, on='FID', how='inner')

    ctr_df = both_df.drop([
'at_entry_path',
'scheduled_path_x',
'scheduled_path_y',
'first_filed_path_x',
'first_filed_path_y',
'last_filed_path_x',
'last_filed_path_y',
'ACID_x',
'ACID_y',
'ORIG_TIME_x',
'ORIG_TIME_y',
'WAYPOINTS_x',
'WAYPOINTS_y',

'DEP_TIME_y',
'ARR_TIME_y',
'DEPT_APRT_y',
'ARR_APRT_y',
'ACFT_TYPE_y',

'POSIT_TIME', 'position'
        ], axis=1)

    ctr_df.rename( {
            'DEP_TIME_x'  : 'DEP_TIME',
            'ARR_TIME_x'  : 'ARR_TIME',
            'DEPT_APRT_x' : 'DEPT_APRT',
            'ARR_APRT_x'  : 'ARR_APRT',
            'ACFT_TYPE_x' : 'ACFT_TYPE',
        }, axis=1, inplace=True)

    return(ctr_df)

# ==========================================================================

def make_bogus_before_entry(ctr_df):

    ctr_df['at_entry_within_path'] = LineString()
    ctr_df['at_entry_within_dist'] = 0

    ctr_df['FLIGHT_INDEX'] = 0  ## HELP <<<<<<<<<<<<<<

    ctr_df.drop([
                   'ORIG_TIME',
                   'WAYPOINTS',
                   'scheduled_path',
                   'first_filed_path',
                   'last_filed_path',
                   #  'flown_path',  HELP: needs to be here to drop later
                   # by  fpostg?
                         ], axis=1, inplace=True)

    return(ctr_df)

# ======================================================================

# note: this may fail and return None, which is cleaned by the dropna()
# ALSO, lots of duplicates, TODO: remove dups

def form_linestring(row):

    # ---- apparently, dep and arr apts are in waypoints

    # ---- 1.  form list of all waypoints (as shapely Point()s)

    try:
        wpts = row['WAYPOINTS'].split()

        pts = list( map( lambda x:
              Point(
                 float(x.split('/')[1])/(-60.0),
                 float(x.split('/')[0])/  60.0
              ), wpts ) )
    except:
        return(None)     # something messed up, fail

    #  and put them together in a (shapely) linestring

    try:
        path_ls = LineString(pts)
    except:
        print("bad Linestring, len=", len(pts), row['DEPT_APRT'], row['ARR_APRT'])
        return(None)     # bad shapely linestring ( < 2 points?)

    return(path_ls)

