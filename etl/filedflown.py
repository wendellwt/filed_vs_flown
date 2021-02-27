#!/home/data/local/bin/python3.7

# ####################################################################### #
#        calculate distance of scheduled and flown flight paths           #
# ####################################################################### #

descr = \
"""for one arrival airport, generate distances for filed and flown paths
and output to PostGIS at CSSI and Oracle"""

import sys
import json
import toml
import pandas as pd
import pickle
import argparse
import datetime
import geopandas as gpd
from shapely.geometry import LineString
import code           # <<<<<<<<<<<

# our own:
import foracle
import fpostg
import fcrop
import elapsed

# ####################################################################### #
#                               argparse                                  #
# ####################################################################### #

parser = argparse.ArgumentParser(description=descr)

# for TESTING, use different date:
parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 4),
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

#parser.add_argument('-w', '--write_postigs', action='store_const', const=True,
#            help="write to postigs", default=False )

args = parser.parse_args()

y_m   = args.date.strftime("%Y_%m")
y_m_d = args.date.strftime("%Y_%m_%d")

# =========================================================================

from shapely.wkt import loads

# ---- and read in adaptation

adapt = toml.load("adaptation.toml")

# Q: Move these to fcrop.py?????
tracon_shp_dir = "/home/data/wturner/shapefiles/"
tracon_shapefile = tracon_shp_dir + adapt[args.airport]['tracon']

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
         [ (c, '1sttier') for c in adapt[args.airport]['1sttier'] ] + \
         [ (c, '2ndtier') for c in adapt[args.airport]['2ndtier'] ]

# # >>>>>>>> special testing today:
# artccs = [ ('ZMP', '1sttier'), ] + \
#          [ ('ZAU', '2ndtier'), ]

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

#   pandas                    oracle                     postgis
#   -------------             -----------------          ------------------
#  'ACID'                     ACID                       acid
#  'FID'                                                 fid
#  'FLIGHT_INDEX'
#  'DEP_TIME'                 DEPT_TIME                  dep_time
#  'ARR_TIME'                 ARR_TIME                   arr_time
#  'DEPT_APRT'                ORIG                       dep_apt
#  'ARR_APRT'                 DEST                       arr_apt
#  'corner'                   CORNERPOST                 corner
#  'OPSDAY'                   OPSDAY                     opsday
#  'artcc'                    ARTCC                      artcc
#  'ACFT_TYPE'                                           ac_type
#   ----                      ARTCC_LEVEL
#
#  'scheduled_upto_dist'      SCHED_DIST_TO              scheduled_upto_dist
#  'first_filed_upto_dist'    FIRST_FILED_DIST_TO        first_filed_upto_dist
#  'last_filed_upto_dist'     LAST_FILED_DIST_TO         last_filed_upto_dist
#  0                          PRIOR_ENTRY_FILED_DIST_TO
#  'flown_upto_dist'          ACTUAL_FLOWN_DIST_TO       flown_upto_dist
#
#  'scheduled_within_dist'    SCHED_DIST_IN              scheduled_within_dist
#  'first_filed_within_dist'  FIRST_FILED_DIST_IN        first_filed_within_dist
#  'last_filed_within_dist'   LAST_FILED_DIST_IN         last_filed_within_dist
#  'at_entry_within_dist'     PRIOR_ENTRY_FILED_DIST_IN  at_entry_within_dist
#  'flown_within_dist'        ACTUAL_FLOWN_DIST_IN       flown_within_dist
#
#  'scheduled_upto_path'                                 scheduled_upto_geog
#  'first_filed_upto_path'                               first_filed_upto_geog
#  'last_filed_upto_path'                                last_filed_upto_geog
#  'flown_upto_path'                                     flown_upto_geog
#
#  'scheduled_within_path'                               scheduled_within_geog
#  'first_filed_within_path'                             first_filed_within_geog
#  'last_filed_within_path'                              last_filed_within_geog
#  'at_entry_within_path'                                at_entry_within_geog
#  'flown_within_path'                                   flown_within_geog
#
#  'flown_path'

# special case:
#    if artcc == 'ZZZ' then all within paths and distances are for the
#          entire flight from departure to arrival tracon entry

# ====================================================================

def delete_from_oracle_flight_level(ctr):

    opsday = args.date.strftime("%Y-%m-%d")

    foracle.clean_oracle(opsday, ctr, args.verbose)

# ====================================================================

def output_to_oracle_flight_level(center_df, tier):

    # print("about to drop")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # drop cols CP doesn't want
    ora_output_df = center_df.drop([ 'FID', 'FLIGHT_INDEX', 'ACFT_TYPE',
      'scheduled_upto_path',
      'first_filed_upto_path',
      'last_filed_upto_path',
      'flown_upto_path',
      'scheduled_within_path',
      'first_filed_within_path',
      'last_filed_within_path',
      'at_entry_within_path',
      'flown_within_path',
      'flown_path'
      ], axis=1)

    ora_output_df['ARTCC_LEVEL'] = tier

    # print("about to rename")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    ora_output_df.rename( {
        'DEPT_APRT'         : 'ORIG',
        'ARR_APRT'          : 'DEST',
        'DEP_TIME'          : 'DEPT_TIME',
        'corner'            : 'CORNERPOST',

        'scheduled_upto_dist'      : 'SCHED_DIST_TO',
        'first_filed_upto_dist'    : 'FIRST_FILED_DIST_TO',
        'last_filed_upto_dist'     : 'LAST_FILED_DIST_TO',
        #0                         : 'PRIOR_ENTRY_FILED_DIST_TO',
        'flown_upto_dist'          : 'ACTUAL_FLOWN_DIST_TO',

        'scheduled_within_dist'    : 'SCHED_DIST_IN',
        'first_filed_within_dist'  : 'FIRST_FILED_DIST_IN',
        'last_filed_within_dist'   : 'LAST_FILED_DIST_IN',
        'at_entry_within_dist'     : 'PRIOR_ENTRY_FILED_DIST_IN',
        'flown_within_dist'        : 'ACTUAL_FLOWN_DIST_IN',

        }, axis=1, inplace=True)

    # print("ora_output_df")
    # print(ora_output_df)
    # print(ora_output_df.columns)
    # print("about to write to ora")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    ## TODO: delete from <tbl> where opsday = xxx and center = xxx

    foracle.write_to_flight_level(ora_output_df, args.verbose)

    # print("just wrote to ora")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

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

    first_scheduled_df['scheduled_path'] = first_scheduled_df.apply( lambda row: fcrop.form_linestring(row), axis=1)
    first_scheduled_df.dropna(inplace=True)

    # +++++++++++++++++++++++ first_filed_path +++++++++++++++++++++++++++

    # b1. get just schedules with ORIG_TIME before departure

    all_filed_df = sched_df.loc[sched_df['SOURCE_TYPE'] == 'F']

    # b2. get the one with a max orig_time

    first_filed_df = all_filed_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    # b3. and make a linestring of it while we're here

    first_filed_df['first_filed_path'] = first_filed_df.apply( lambda row: fcrop.form_linestring(row), axis=1)
    first_filed_df.dropna(inplace=True)

    # +++++++++++++++++++++++ last_filed_path +++++++++++++++++++++++++++

    # b1. get just schedules with ORIG_TIME before departure

    all_b4_dep_df = sched_df.loc[sched_df['ORIG_TIME'] < sched_df['DEP_TIME']]  # fix?
    #all_b4_dep_df = sched_df.loc[sched_df['ORIG_TIME'] >= sched_df['DEP_TIME']]  # BUG <<<<<<<<<<<<

    # b2. get the one with a max orig_time

    last_b4_dep_df = all_b4_dep_df.sort_values("ORIG_TIME").groupby("FID", as_index=False).first()

    # b3. and make a linestring of it while we're here

    last_b4_dep_df['last_filed_path'] = last_b4_dep_df.apply( lambda row: fcrop.form_linestring(row), axis=1)
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

def output_postgis(ctr_df):

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

    # print("after renames for postgis")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    ## TODO: delete from <tbl> where opsday = xxx and center = xxx

    fpostg.write_ff_to_postgis_cssi(y_m, ctr_df)

# =========================================================================

def finalize_cols(ctr_df, ctr):

    # put this in postgis also, just to keep them consistent...
    ctr_df['OPSDAY'] = ctr_df['ARR_TIME'].apply(lambda dt:
         (dt - datetime.timedelta(hours=8))
                 .replace(hour=0,minute=0,second=0)
                 .date())   # and remove any _hint_ of timezones

    ctr_df['artcc'] = ctr   # and all of this data gets this artcc

    return(ctr_df)

# ####################################################################### #
#                                  main                                   #
# ####################################################################### #

fall = elapsed.Elapsed()
ro = elapsed.Elapsed()

# ==== a. read _all_ schedules from oracle

sched_df, just_fids = get_sched_data_from_oracle(args.date, args.airport)

# ==== b. get scheduled paths before departure

all_scheds_df = make_all_scheds(sched_df)

# ==== c. retrieve TZ (flown) data from oracle

flown_pts_df, flown_ls_df = get_flown_data(just_fids)

# print("beginning corners")

flown_ls_df['corner'] = flown_ls_df['flown_path'].apply(
                     lambda ls: closest_corner(ls))

ro.end("read oracle")

# ++++++++++++++++++++++++++ Summary feb20 ++++++++++++++++++++++++++
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
# ++++++++++++++++++++++++++         ++++++++++++++++++++++++++

# print("end of setup")

# >>>>>>>>>>>>>>>>>>>> begin loop on artccs <<<<<<<<<<<<<<<<<<<<<<<<<

import fjson

for ctr, tier in artccs:

    print("== ", ctr, tier)
    #delete_from_oracle_flight_level(ctr) # <<<<<<<<<<<<<<<<<<<<<<

    ce = elapsed.Elapsed()

    # ==== a. form base of this center output df

    ctr_df = pd.merge(all_scheds_df, flown_ls_df, on='FID', how='inner')

    # ==== b. get ARTCC polygon of interest

    fcrop.read_masking_shapes(ctr, tier, tracon_shapefile, artccs, args.verbose)

    # ==== ==== ====

    #  and get an intersection column
    # NOTE: is is not a GeoPandas df, but a Pandas df with geometry columns

    ctr_df = fcrop.get_all_withins(ctr_df, ctr)

    #if ctr == 'ZMP' or ctr == 'ZAU':

    #    fjson.output_json_to_file(ctr_df, ctr, center_minus_tracon_shp, y_m_d)

    #    print(ctr_df)
    #    print(ctr_df.columns)
    #    print("all within paths")
    #    code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ==== ==== ==== (cp wants these) each path DIFFERENCE with tracon

    if ctr != 'ZZZ':
        ctr_df = fcrop.get_all_uptos(ctr_df)
    else:
        ctr_df = fcrop.fake_all_uptos(ctr_df)

    # ==== ==== ==== h. before entry paths intersected by that poly

    # note: for artcc == real, this is the _one_ schedule before entry
    if ctr != 'ZZZ':

        ctr_df = fcrop.get_before_entry_single_artcc(ctr_df,
                                                     all_scheds_df, flown_pts_df)
    else:

        ctr_df = fcrop.make_bogus_before_entry(ctr_df)

    # ==== k. final cleanup & prep for d.b. writes

    ctr_df = finalize_cols(ctr_df, ctr)

    ce.end("center calculations")

    # ==== m. output

    ou = elapsed.Elapsed()

    if ctr != 'ZZZ':
        if not args.skip_oracle:
            #delete_from_oracle_flight_level(ctr)
            output_to_oracle_flight_level(ctr_df, tier)

    output_postgis(ctr_df)

    ou.end("databases written")

fall.end("finished " +  args.airport + ' ' +  args.date.strftime('%Y-%m-%d'))

