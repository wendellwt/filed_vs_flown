#!/home/data/local/bin/python3.7

# ####################################################################### #
#        calculate distance of scheduled and flown flight paths           #
# ####################################################################### #

descr = \
"""for one arrival airport, generate distances for filed and flown paths"""

import sys
import json
import toml
import pandas as pd
import pickle
import argparse
import datetime
import geopandas as gpd
from shapely.geometry import shape, Point, LineString

# our own:
import foracle
import fpostg
import elapsed

import code                     # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# ####################################################################### #
#                               argparse                                  #
# ####################################################################### #

parser = argparse.ArgumentParser(description=descr)

# for TESTING, use different date:
parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 10),
            type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='start date yyyy-mm-dd')

parser.add_argument('-a', '--airport', type=str,
            help="arrival airport", default="DEN")

parser.add_argument('-v', '--verbose', action='store_const', const=True,
            help="verbosity", default=False )

parser.add_argument('-p', '--pickle', action='store_const', const=True,
            help="use pickle instead of oracle", default=False )

parser.add_argument('-s', '--skip_oracle', action='store_const', const=True,
            help="skip writing to oracle", default=False )

parser.add_argument('-w', '--write_postigs', action='store_const', const=True,
            help="write to postigs", default=False )

args = parser.parse_args()

y_m   = args.date.strftime("%Y_%m")
y_m_d = args.date.strftime("%Y_%m_%d")

# =========================================================================

from shapely.wkt import loads

# ---- and read in adaptation

adapt = toml.load("adaptation.toml")

tracon_shp_dir = "/home/data/wturner/shapefiles/"
tracon_shapefile = tracon_shp_dir + adapt[args.airport]['tracon']
conus_shapefile  = tracon_shp_dir + "conus.shp"

# ---- make table of corners

cnr_lst = [ adapt[args.airport][direc] for direc in ( "ne", "se", "sw", "nw")]

corners = {
 "ne": loads(fpostg.get_corner_pos( adapt[args.airport]['ne'] )),
 "se": loads(fpostg.get_corner_pos( adapt[args.airport]['se'] )),
 "sw": loads(fpostg.get_corner_pos( adapt[args.airport]['sw'] )),
 "nw": loads(fpostg.get_corner_pos( adapt[args.airport]['nw'] ))
}

# ---- make list of artcc's

artccs = [ (adapt[args.airport]['parent'], 'parent'),             ] + \
         [ ('ZZZ', 'full')                                        ] + \
         [ (c, '1sttier') for c in adapt[args.airport]['1sttier'] ] # + \

#artccs = [ (adapt[args.airport]['parent'], 'parent'),             ]
#artccs = [ ('ZZZ', 'full') ]

# not yet:[ (c, '2ndtier') for c in adapt[args.airport]['2ndtier'] ]

# ####################################################################### #
#                 schedule path processing routines                       #
# ####################################################################### #

# ---- retrieve _all_ scheduled data from route_yyyymmdd@extr1 tables,
#      and filter by arrival airport

def get_sched_data_from_oracle(act_date, arr_apt):

    print("querying oracle for sched data")

    ro = elapsed.Elapsed()

    if args.pickle:
        arrivals_df = pickle.load( open(
                                  "files/p_filed_" + y_m_d + "_df.p", "rb" ))
    else:
        arrivals_df = foracle.read_ops_day_data(act_date, arr_apt, args.verbose)

        pickle.dump( arrivals_df, open(
                                  "files/p_filed_" + y_m_d + "_df.p","wb" ))

    # ---- 2. get distinct flight id's

    just_fids_df = arrivals_df.drop_duplicates(subset=['FID'])
    just_fids = just_fids_df['FID'].to_list()
    clean_fids = [int(x) for x in just_fids if str(x) != 'nan']

    ro.end("read schedule data")

    if args.verbose: print("arrivals_df")
    if args.verbose: print(arrivals_df)

    return(arrivals_df, clean_fids)

# ======================================================================

# note: this may fail and return None, which is cleaned by the dropna()
# ALSO, lots of duplicates, TODO: remove dups

def form_linestring(row, verbose=False):

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

# ======================================================================

# -----------------------  read shapefile of artcc and tracon

import shapefile
from shapely import wkb
from shapely.geometry import mapping

# feb20: if ctr = ZZZ, then return ??? and tracon shapefile

def read_artcc_and_tracon(ctr):

    # 1) read shapefile using with PyShp
    # https://gis.stackexchange.com/questions/113799/how-to-read-a-shapefile-in-python

    tracon_esri = shapefile.Reader(tracon_shapefile)

    # first feature of the shapefile
    tracon_feature = tracon_esri.shapeRecords()[0]

    tracon_geom = tracon_feature.shape.__geo_interface__

    # 2) conversion to Shapely geometry (with the shape function)

    tracon_shape = shape(tracon_geom)

    if ctr == 'ZZZ':   # special check for full flight

        # pretend artcc is entire conus

        conus_esri = shapefile.Reader(conus_shapefile)
        conus_feature = conus_esri.shapeRecords()[0]
        conus_geom = conus_feature.shape.__geo_interface__
        conus_shape = shape(conus_geom)
        conus_minus_tracon_shape = conus_shape.difference(tracon_shape)

        return(conus_minus_tracon_shape, tracon_shape)   # feb20

    ctr_wkb = fpostg.get_shape_of_ctr(ctr, args_verbose=False)

    ctr_shape = wkb.loads(ctr_wkb[0][0], hex=True)

    # and have _shapely_ take the difference:

    center_minus_tracon_shape = ctr_shape.difference(tracon_shape)

    return(center_minus_tracon_shape, tracon_shape)

# =========================================================================

from geopy import distance

# @@@@@@@@@@@@@  calc G.C. DISTANCE (length) of one linestring

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
            print("HELP: don't know how to handle:", ls_path.geom_type)
            # print(ls_path) # (see below)
            return(0)
            #sys.exit(1)

    return(0)  # ???

# GEOMETRYCOLLECTION (POINT (-94.05 36.75), LINESTRING (-86.64 34.13, ...
# -----------------------------------------------------------------

def help_gc_length_one_segment(ls_path):

    if ls_path.is_empty:
        return(0)

    #print(ls_path)
    #print(ls_path.geom_type)

    if ls_path.geom_type=="MultiLineString":
        print("HELP: MultiLineString")
        return(99)

    lon_lat = list(ls_path.coords)
    # print(lon_lat)

    # If you pass coordinates as positional args, please make sure that the
    # order is (latitude, longitude) or (y, x) in Cartesian terms.

    # swap each pair of elements to get right order for geopy's distance()
    lat_lon = [(item[1], item[0]) for item in lon_lat]
    # print(lat_lon)

    segments = [(lat_lon[k], lat_lon[k + 1]) for k in range(len(lat_lon)-1)]
    # print(segments)

    dsegs = [distance.distance(seg[0], seg[1]).nautical for seg in segments]

    # print(sum(dsegs))

    return(sum(dsegs))

# =========================================================================

def get_at_entry_sch_paths(all_scheds_df, flw_pts_df, center_shp):

    #ae = elapsed.Elapsed()

    # ---- first, get all TZ within the artcc:

    tz_within = flw_pts_df.loc[flw_pts_df['position'].intersects(center_shp)]

    # ---- second, get the first POSIT_TIME of each FID

    first_tz_within = tz_within.sort_values("POSIT_TIME").groupby("FID", as_index=False).last()

    # ---- third, match those FIDs with the original SCHED ones

    sched_with_tz_df = pd.merge(first_tz_within, all_scheds_df, on='FID', how='inner')

    # ---- fourth, keep just the rows where orig_time <= first tz time

    scheds_outside_df = sched_with_tz_df.loc[sched_with_tz_df['ORIG_TIME'] < sched_with_tz_df['POSIT_TIME'] ]

    # and get the last (largest) times of those

    at_entry_df = scheds_outside_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    #ae.end("at_entry df")

    return(at_entry_df)

# ========================================================================
def closest_corner(ls):

    dd = { 'ne': ls.distance(corners['ne']),
           'se': ls.distance(corners['se']),
           'sw': ls.distance(corners['sw']),
           'nw': ls.distance(corners['nw']) }

    return(min(dd, key=dd.get))  # may as well be random !!! :-(

# ========================================================================

import pytz

def output_to_oracle_flight_level(center_df, tier):

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # drop cols CP doesn't want
    ora_output_df = center_df.drop([ 'FID', 'b4_dep_path',
                                    'b4_ent_path', 'flw_path',
                                    'b4_dep_up_to_path', 'flw_up_to_path',
                                    'ACFT_TYPE_x',
                                    ], axis=1)

    ora_output_df['ARTCC_LEVEL'] = tier

    ora_output_df.rename( {
        'DEPT_APRT'         : 'ORIG',
        'ARR_APRT'          : 'DEST',
        'DEP_TIME'          : 'DEPT_TIME',
        'corner'            : 'CORNERPOST',
        'b4_dep_dist'       : 'LAST_FILED_DIST',
        'b4_ent_dist'       : 'BEFORE_ENTRY_DIST',
        'flw_dist'          : 'FLOWN_DIST',
        'b4_dep_up_to_dist' : 'LAST_FILED_UP_TO_DIST',
        'flw_up_to_dist'    : 'FLOWN_UP_TO_DIST'
        }, axis=1, inplace=True)

        # these are ok:
        #ACID'     : 'ACID',
        #ARR_TIME' : 'ARR_TIME',

    #print("ora_output_df")
    #print(ora_output_df)
    #print(ora_output_df.columns)

    foracle.write_to_flight_level(ora_output_df, args.verbose)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# ========================================================================

# old/current: get the (one) path before departure and call it sched_path

# feb20: form xxx_path for:
#    * scheduled    === first record with source_type='S'
#    * first_filed  === first record with source_type='F'
#    * last_filed   === latest record (any type) with orig_time < dep_time

def make_all_scheds(sched_df):

    bb = elapsed.Elapsed()

    # +++++++++++++++++++++++ scheduled_path +++++++++++++++++++++++++++

    # b1. get just schedules with record type 'S'

    # print(sched_df.columns)
    all_scheduled_df = sched_df.loc[sched_df['SOURCE_TYPE'] == 'S']

    # b2. get the one with a max orig_time

    first_scheduled_df = all_scheduled_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    # b3. and make a linestring of it while we're here

    first_scheduled_df['scheduled_path'] = first_scheduled_df.apply( lambda row: form_linestring(row, False), axis=1)
    first_scheduled_df.dropna(inplace=True)

    # +++++++++++++++++++++++ first_filed_path +++++++++++++++++++++++++++

    # b1. get just schedules with ORIG_TIME before departure

    all_filed_df = sched_df.loc[sched_df['SOURCE_TYPE'] == 'F']

    # b2. get the one with a max orig_time

    first_filed_df = all_filed_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    # b3. and make a linestring of it while we're here

    first_filed_df['first_filed_path'] = first_filed_df.apply( lambda row: form_linestring(row, False), axis=1)
    first_filed_df.dropna(inplace=True)

    # +++++++++++++++++++++++ last_filed_path +++++++++++++++++++++++++++

    # b1. get just schedules with ORIG_TIME before departure

    all_b4_dep_df = sched_df.loc[sched_df['ORIG_TIME'] >= sched_df['DEP_TIME']]

    # b2. get the one with a max orig_time

    last_b4_dep_df = all_b4_dep_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    # b3. and make a linestring of it while we're here

    last_b4_dep_df['last_filed_path'] = last_b4_dep_df.apply( lambda row: form_linestring(row, False), axis=1)
    last_b4_dep_df.dropna(inplace=True)

    # +++++++++++++++++++++++

    bb.end("paths before depart")

   #feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # FIXME: does this DROP all flights that DON'T HAVE ALL TYPES OF FLIGHTS???
    # FIXME: does this DROP all flights that DON'T HAVE ALL TYPES OF FLIGHTS???

    all_scheds_df = pd.merge(first_scheduled_df, first_filed_df, on='FID', how='inner')
    all_scheds_df = pd.merge(all_scheds_df, last_b4_dep_df, on='FID', how='inner')

   #feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    all_scheds_df.drop([
        'ACID_x',
        'FLIGHT_INDEX_x',
        'SOURCE_TYPE_x',
        'DEP_TIME_x',
        'ARR_TIME_x',
        'DEPT_APRT_x',
        'ARR_APRT_x',
        'ACFT_TYPE_x',
        'WAYPOINTS_x',
        'ORIG_TIME_x',

        'ACID_y',
        'FLIGHT_INDEX_y',
        'SOURCE_TYPE_y',
        'DEP_TIME_y',
        'ARR_TIME_y',
        'DEPT_APRT_y',
        'ARR_APRT_y',
        'ACFT_TYPE_y',
        'WAYPOINTS_y',
        'ORIG_TIME_y',

        'SOURCE_TYPE', # possibly useful if kept around on a per-path basis
        'FLIGHT_INDEX',# Q: is this useful later on???

        #'ORIG_TIME',   # at_entry is going to need this
        #'WAYPOINTS',   # at_entry is going to need this

    ], axis=1, inplace=True)


    if args.verbose: print("all_scheds_df")
    if args.verbose: print(all_scheds_df)
    if args.verbose: print(all_scheds_df.columns)

    #feb20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    return(all_scheds_df)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def get_flown_data(just_fids):

    # cc = elapsed.Elapsed()

    # ---- c.1) fetch all FIDs from Oracle/TFMS

    if args.pickle:
        full_tz_df = pickle.load( open(
                                  "files/p_full_tz_" + y_m_d + "_df.p", "rb" ))
    else:

        # NOT SORTED BY POSIT_TIME !!
        full_tz_df = foracle.get_all_tz_using_temp(args.date, just_fids,
                                                   args.verbose)

        pickle.dump( full_tz_df, open(
                                 "files/p_full_tz_" + y_m_d + "_df.p","wb" ))

    # ---- remove duplicated time fields

    tz_df = full_tz_df.drop_duplicates(subset=["FLIGHT_INDEX", "POSIT_TIME"])

    # ---- c.3) make a (real) GeoDF of the flown path/track

    flown_pts_df = gpd.GeoDataFrame(
        tz_df, geometry=gpd.points_from_xy(tz_df.LON, tz_df.LAT))

    flown_pts_df.drop(['LAT', 'LON'], axis=1, inplace=True)
    flown_pts_df.rename( {'geometry' : 'position'}, axis=1, inplace=True)

    # Q: do we need to sort by POSIT_TIME ???
    # this is a Series

    # TODO: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #   add row containing position of departure airport with FAKE POSIT_TIME
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    posit_time_df = flown_pts_df.sort_values(by='POSIT_TIME')

    flown_ls_sr = posit_time_df.groupby(['FID'])['position']        \
                              .apply(lambda p:
                  LineString(p.tolist()) if len(p.tolist()) > 2 else LineString())

    flown_ls_df = pd.DataFrame( {'FID'        : flown_ls_sr.index,
                                 'flown_path' : flown_ls_sr.values} )

    # cc.end("get flown data")

    if args.verbose: print("flown_pts_df")
    if args.verbose: print(flown_pts_df)

    if args.verbose: print("flown_ls_df")
    if args.verbose: print(flown_ls_df)

    return(flown_pts_df, flown_ls_df)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def merge_everything(last_b4_dep_df, at_entry_df, flown_ls_df):

    # clean up columns
    b4_dep_ready_df = last_b4_dep_df.drop([
                    'FLIGHT_INDEX', 'WAYPOINTS', 'SOURCE_TYPE', 'ORIG_TIME',
                    'sched_path'], axis=1)

    at_entry_ready_df = at_entry_df.drop([
           'FLIGHT_INDEX_x', 'ACID_x', 'POSIT_TIME', 'position', 'ACID_y',
           'FLIGHT_INDEX_y', 'ORIG_TIME', 'SOURCE_TYPE', 'DEP_TIME', 'ARR_TIME',
           'DEPT_APRT', 'ARR_APRT', 'WAYPOINTS',
           'sched_path'], axis=1)

    flown_ready_df = flown_ls_df.drop('flown_path', axis=1)

    center_df = pd.merge(b4_dep_ready_df, at_entry_ready_df, on='FID', how='inner')
    center_df = pd.merge(center_df,  flown_ready_df,     on='FID', how='inner')

    center_df.drop(['ACFT_TYPE_y'], axis=1, inplace=True)

    return(center_df)

# ========================================================================

def output_json_to_file(center_df, ctr, artcc_shp):

    # for TESTING, get rid of large columns...
    # and keep JUST ONE geom column
    trim_df = center_df.drop(['FID', 'DEP_TIME',
                    'b4_dep_path', 'b4_dep_dist',
                    #'b4_ent_path', 'b4_ent_dist'
                              ], axis=1)

    help_output_corner(trim_df, 'ne', ctr, artcc_shp)
    help_output_corner(trim_df, 'se', ctr, artcc_shp)
    help_output_corner(trim_df, 'sw', ctr, artcc_shp)
    help_output_corner(trim_df, 'nw', ctr, artcc_shp)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# =========================================================================

def help_output_corner(trim_df, cnr, ctr, artcc_shp):

    ne_df = trim_df.loc[trim_df['corner']==cnr]

    # HELP >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ne_15z_df = ne_df.loc[ne_df['ARR_TIME'] >= datetime.datetime(2020,3,2,15,0,0)]

    # ==== method 1. write GeoDataFrame to disk (meaning paths only)
    # <<<<<<<<<<<<<<<<<<< LAME
    # ne_15z_gf = gpd.GeoDataFrame( ne_15z_df, geometry='flw_path')
    # ne_15z_gf.rename( {'geometry' : 'flw_path'}, axis=1, inplace=True)
    # fn = "cnr_" + cnr + ".gjsn"
    # ne_15z_gf.to_file(fn, driver="GeoJSON")
    # print("fn=", fn)
    # <<<<<<<<<<<<<<<<<<< LAME

    # ==== method 2. add colors, and FC including artcc

    if len(ne_15z_df) == 0:   # empty === uninteresting
        return

    paths_gj = form_feature_collection(ne_15z_df, artcc_shp)

    fn = "files/fc_" + cnr + '_' + ctr + '_' + y_m_d + ".gjsn"

    with open(fn, "w") as fd:
        fd.write( json.dumps(paths_gj) )

    #print("fn=", fn)

# ====================================================================

from geojson import Feature, FeatureCollection

# note: input is a df, not a gf

def form_feature_collection(flts_df, artcc_shp):

    features = [ Feature(geometry   = mapping(artcc_shp),
                         id         = 1,
                         properties = { "name" : 'ARTCC'}
                        ), ]
    help_id = 4

    for index, row in flts_df.iterrows():

        # http://geojson.tools/ shows colors from properties:

        flw_feat = Feature(geometry   = mapping(row['flw_path']),
                           id         = help_id,
                           properties =
                                 { "acid"    : row['ACID'],
                                   "corner"  : row['corner'],
                                   "color"   : "magenta",
                                   #"arr_time" : row['arr_time'].replace(' ','T'),
                                 })

        features.append(flw_feat)
        help_id += 1

        ate_feat = Feature(geometry   = mapping(row['b4_ent_path']),
                           id         = help_id,
                           properties =
                                 { "acid"    : row['ACID'],
                                   "corner"  : row['corner'],
                                   "color"   : "blue",
                                   #"arr_time" : row['arr_time'].replace(' ','T'),
                                 })

        features.append(ate_feat)
        help_id += 1

    feature_collection = FeatureCollection(features)
    return(feature_collection)

# ==========================================================================

def output_postgis(ctr_df, ctr_name, center_minus_tracon_shp):

    # q: need to explicitly make lower case?
    ctr_df.rename( {
        'FID'         : 'fid',
        'ACID'        : 'acid',
        'ACFT_TYPE_x' : 'ac_type',   # HELP: is this right
        'ACFT_TYPE'   : 'ac_type',   # HELP: why is this needed???
        'DEP_TIME'    : 'dep_time',
        'ARR_TIME'    : 'arr_time',
        'DEPT_APRT'   : 'dep_apt',
        'ARR_APRT'    : 'arr_apt',
        }, axis=1, inplace=True)

    ctr_df['artcc'] = ctr_name   # and all of this data gets this artcc

    fpostg.write_ff_to_postgis_cssi(y_m, ctr_df)

# ++++++++++++++++++++++++++++++++++++++++++++

# WARNING: what shape to use here???

def do_intersect(path_ls):
    int_path = path_ls.intersection(center_minus_tracon_shp)
    int_path = int_path[0] if int_path.geom_type == "MultiLineString" else int_path
    return int_path

# ++++++++++++++++++++++++++++++++++++++++++++

# WARNING: what shape to use here???

def do_difference(path_ls):

    int_path = path_ls.difference(center_minus_tracon_shp)
    int_path = int_path[0] if int_path.geom_type == "MultiLineString" else int_path
    return int_path

# ####################################################################### #
#                                  main                                   #
# ####################################################################### #

all = elapsed.Elapsed()

# ==== a. read _all_ schedules from oracle

sched_df, just_fids = get_sched_data_from_oracle(args.date, args.airport)

# ==== b. get scheduled paths before departure

all_scheds_df = make_all_scheds(sched_df)

# ==== c. retrieve TZ (flown) data from oracle

flown_pts_df, flown_ls_df = get_flown_data(just_fids)

cn = elapsed.Elapsed()
# print("beginning corners")

flown_ls_df['corner'] = flown_ls_df['flown_path'].apply(
                     lambda ls: closest_corner(ls))

cn.end("find all corners")

# %%%%%%%%%%%%%%%%%%%%%%%%%% Summary feb20 %%%%%%%%%%%%%%%%%%%%%%%%%%
# all_scheds_df:
#    * scheduled    === first record with source_type='S'
#    * first_filed  === first record with source_type='F'
#    * last_filed   === latest record (any type) with orig_time < dep_time
# flown_ls_df:
#    * flown_path   === path of TZ records
#    * corner       === closest flown corner
# at_entry_df:  (to be added later, if doing an individual artcc)
#    * b4_ent_path  === latest record (any type) with orig_time < posit_time of
#                       first TZ point inside artcc
# %%%%%%%%%%%%%%%%%%%%%%%%%%         %%%%%%%%%%%%%%%%%%%%%%%%%%

print("end of setup")
#feb20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# >>>>>>>>>>>>>>>>>>>> begin loop on artccs <<<<<<<<<<<<<<<<<<<<<<<<<

for ctr, tier in artccs:

    print("==== ", ctr, tier)
    ce = elapsed.Elapsed()

    # ==== a. form base of this center output df

    ctr_df = pd.merge(all_scheds_df, flown_ls_df, on='FID', how='inner')

    #print(ctr_df)
    #print(ctr_df.columns)
    #print("CHECK ctr_df columns")
    #feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ==== b. get ARTCC polygon of interest

    center_minus_tracon_shp, tracon_shp = read_artcc_and_tracon(ctr)

    # print("have ctr and tracon shapes")

    # ==== ==== ====

    #  and get an intersection column
    # NOTE: is is not a GeoPandas df, but a Pandas df with a geometry column

    # ==== ==== ==== each path INTERSECTED with artcc shape
    # NOTE: if artcc is real, these are the WITHIN,
    #       if artcc is zzz, these are the FULL (but still without the tracon)

    ctr_df['scheduled_within_path'] = ctr_df['scheduled_path'       ].apply(lambda p: do_intersect(p))
    ctr_df['scheduled_within_dist'] = ctr_df['scheduled_within_path'].apply(lambda p: gc_length(p))

    ctr_df['first_filed_within_path'] = ctr_df['first_filed_path'       ].apply(lambda p: do_intersect(p))
    ctr_df['first_filed_within_dist'] = ctr_df['first_filed_within_path'].apply(lambda p: gc_length(p))

    ctr_df['last_filed_within_path'] = ctr_df['last_filed_path'       ].apply(lambda p: do_intersect(p))
    ctr_df['last_filed_within_dist'] = ctr_df['last_filed_within_path'].apply(lambda p: gc_length(p))

    ctr_df['flown_within_path'] = ctr_df['flown_path'       ].apply(lambda p: do_intersect(p))
    ctr_df['flown_within_dist'] = ctr_df['flown_within_path'].apply(lambda p: gc_length(p))

    # print(ctr_df)
    # print(ctr_df.columns)
    # print("all within paths")
    #feb20#feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ==== ==== ==== (cp wants these) each path DIFFERENCE with tracon

    ctr_df['scheduled_upto_path'] = ctr_df['scheduled_path'     ].apply(lambda p: do_difference(p))
    ctr_df['scheduled_upto_dist'] = ctr_df['scheduled_upto_path'].apply(lambda p: gc_length(p))

    ctr_df['first_filed_upto_path'] = ctr_df['first_filed_path'     ].apply(lambda p: do_difference(p))
    ctr_df['first_filed_upto_dist'] = ctr_df['first_filed_upto_path'].apply(lambda p: gc_length(p))

    ctr_df['last_filed_upto_path'] = ctr_df['last_filed_path'     ].apply(lambda p: do_difference(p))
    ctr_df['last_filed_upto_dist'] = ctr_df['last_filed_upto_path'].apply(lambda p: gc_length(p))

    ctr_df['flown_upto_path'] = ctr_df['flown_path'     ].apply(lambda p: do_difference(p))
    ctr_df['flown_upto_dist'] = ctr_df['flown_upto_path'].apply(lambda p: gc_length(p))

    # print(ctr_df)
    # print(ctr_df.columns)
    # print("all upto paths")
    #feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ==== ==== ==== h. before entry paths intersected by that poly
    # note: for artcc == real, this is the _one_ schedule before entry

    if ctr != 'ZZZ':
        # get df of rows from sched_df having orig_time last one before artcc entry

        at_entry_df = get_at_entry_sch_paths(all_scheds_df, flown_pts_df,
                                         center_minus_tracon_shp)

        # print("at_entry_df")
        # print(at_entry_df)
        #feb20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # and make a linestring of those waypoints, and get dist

        at_entry_df['at_entry_path'] = at_entry_df.apply( lambda row:
                                    form_linestring(row, False), axis=1)

        # print("at_entry_df + linestrings")
        # print(at_entry_df)
        #feb 20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        at_entry_df['at_entry_within_path'] = at_entry_df['at_entry_path'       ].apply(lambda p: do_difference(p))
        at_entry_df['at_entry_within_dist'] = at_entry_df['at_entry_within_path'].apply(lambda p: gc_length(p))

        both_df = pd.merge(ctr_df, at_entry_df, on='FID', how='inner')

        ctr_df = both_df.drop([
'at_entry_path',
'scheduled_path_x',
'first_filed_path_x',
'ORIG_TIME_x',
'WAYPOINTS_x',
'last_filed_path_x',
'ACID_x',
'scheduled_path_y',
'first_filed_path_y',
'ACID_y',
'ORIG_TIME_y',
'DEP_TIME_y',
'ARR_TIME_y',
'DEPT_APRT_y',
'ARR_APRT_y',
'ACFT_TYPE_y',
'WAYPOINTS_y',
'last_filed_path_y',

'POSIT_TIME', 'position'
        ], axis=1)

        ctr_df.rename( {
            'DEP_TIME_x'  : 'DEP_TIME',
            'ARR_TIME_x'  : 'ARR_TIME',
            'DEPT_APRT_x' : 'DEPT_APRT',
            'ARR_APRT_x'  : 'ARR_APRT',
            'ACFT_TYPE_x' : 'ACFT_TYPE',
        }, axis=1, inplace=True)

        # print(ctr_df)
        # print("new ctr_df with at_entry_within != ZZZ")
        #print(ctr_df.columns)

        #for C in ctr_df.columns.tolist():
        #    print(C, "     ", type(ctr_df[C][0]))

        #feb20  code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    else:

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
                   # by  fpostg
                         ], axis=1, inplace=True)

        # print(ctr_df)
        # print("new ctr_df with at_entry_within = ZZZ")
        #print(ctr_df.columns)

        #for C in ctr_df.columns.tolist():
        #    print(C, "     ", type(ctr_df[C][0]))

        #feb20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ==== k. assemble data elements into output frame

    #OLD: center_df = merge_everything( ctr_df, at_entry_df, flown_ls_df)

    # put this in postgis also, just to keep them consistent...
    ctr_df['OPSDAY'] = ctr_df['ARR_TIME'].apply(lambda dt:
         (dt - datetime.timedelta(hours=8))
                 .replace(hour=0,minute=0,second=0)
                 .replace(tzinfo=pytz.UTC))

    # ==== m. output

    ce.end("center calculations")

    #FIXME: if not args.skip_oracle:
    #FIXME:     output_to_oracle_flight_level(center_df, tier)

    # FIXED DATES used here: output_json_to_file(center_df, ctr, center_minus_tracon_shp)

    # print(ctr_df)
    # print(ctr_df.columns)
    # print("about to write to postgis")
    #feb20 code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    #if args.write_postigs:
    output_postgis(ctr_df, ctr, center_minus_tracon_shp)

all.end("finished " +  args.airport + ' ' +  args.date.strftime('%Y-%m-%d'))


