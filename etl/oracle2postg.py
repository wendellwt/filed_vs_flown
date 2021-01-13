#!/home/data/local/bin/python3.7

# ####################################################################### #
#        calculate distance of scheduled and flown flight paths           #
# ####################################################################### #

descr = \
"""for one day, retrieve all scheduled waypoints from oracle
route_ymd table and make postgis linestrings of them;
also retrieve all tracks from oracle tz_ymd table and make them
into MobilityDB trajectories.  """

import json
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

# ####################################################################### #
#                               argparse                                  #
# ####################################################################### #

parser = argparse.ArgumentParser(description=descr)

parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 10),
            type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='start date yyyy-mm-dd')

parser.add_argument('-a', '--airport', type=str,
            help="arrival airport", default="DEN")

parser.add_argument('-v', '--verbose', action='store_const', const=True,
            help="verbosity", default=False )

parser.add_argument('-p', '--pickle', action='store_const', const=True,
            help="use pickle instead of oracle", default=False )

args = parser.parse_args()

# ---- and adjust args to be in a nice format

# filename of csv file (containing airport and operational day)

#csv_fn = args.airport.lower() + '_' + args.date.strftime("%Y_%m_%d") + ".csv"

ora_ymd  = args.date.strftime("%Y%m%d")
y_m_d    = args.date.strftime("%Y-%m-%d")

sched_tablename = "sched_fvf_" + args.date.strftime("%Y_%m_%d")
flown_tablename = "flown_fvf_" + args.date.strftime("%Y_%m_%d")
temp_tablename  = "tempo_fvf_" + args.date.strftime("%Y_%m_%d")

# ####################################################################### #
#                 schedule path processing routines                       #
# ####################################################################### #

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

# ---- get _all_ scheduled data from route_yyyymmdd@extr1 tables
#      and return df of those and a list of just the FIDs

def get_sched_data_from_oracle():

    print("querying oracle for sched data")
    ro = elapsed.Elapsed()

    if args.pickle:
        sched_df = pickle.load( open( "psched_df.p", "rb" ) )
    else:
        sched_df = foracle.read_ops_day_data(args.date, args.airport, args.verbose)
        pickle.dump( sched_df, open( "psched_df.p","wb" ) )

    if args.verbose: print(sched_df)  # to know when query finished

    # ---- 2. get distinct flight id's

    just_fids_df = sched_df.drop_duplicates(subset=['FID'])
    just_fids = just_fids_df['FID'].to_list()
    clean_fids = [int(x) for x in just_fids if str(x) != 'nan']

    ro.end("read oracle")
    return(sched_df, clean_fids)

# ======================================================================

def make_waypoints_into_linestrings(sched_df):

    ls = elapsed.Elapsed()
    print("creating linestrings, num sched flts:", len(sched_df))

    if args.pickle:
        sched_df = pickle.load( open( "psched_path_df.p", "rb" ) )
    else:
        sched_df['sched_path'] = sched_df.apply(
                           lambda row: form_linestring(row, False), axis=1)
        pickle.dump( sched_df, open( "psched_path_df.p","wb" ) )

    ls.end("create linestrings")
    cl = elapsed.Elapsed()
    if args.verbose: print("done with linestrings")

    sched_df.dropna(inplace=True)

    if args.verbose: print("clean, len=", len(sched_df))
    cl.end("clean na")

    return(sched_df)

# ####################################################################### #
#                                  main                                   #
# ####################################################################### #

# >>>>>>>>>>>>>>>>>>> A) scheduled flight paths <<<<<<<<<<<<<<<<<<<<<<<<<

sched_df, just_fids = get_sched_data_from_oracle()

linest_df = make_waypoints_into_linestrings(sched_df)

fpostg.write_sched_df_as_loop(linest_df, sched_tablename, args.verbose)

# >>>>>>>>>>>>>>>>>>> B) flown flight paths <<<<<<<<<<<<<<<<<<<<<<<<<

# ---- b.1) fetch all FIDs from Oracle/TFMS

tz_df = foracle.get_all_tz_using_temp(args.date, just_fids, args.verbose)

if args.verbose: print("tz_df")
if args.verbose: print(tz_df)

pickle.dump(tz_df, open("ptz_df.p","wb" ) )  # just in case we need it

# MobilityDB doesn't like having duplicated time fields
no_dups = tz_df.drop_duplicates(subset=["FLIGHT_INDEX", "POSIT_TIME"])

# ---- b.2) write to temp postgis table

num_written = fpostg.write_tz_to_temp_postgis_table(no_dups, temp_tablename)

# ---- b.3) using temp table, write mdb trajectories

fpostg.drop_create_flown(flown_tablename)

fpostg.temp_points_table_to_mdb_table(temp_tablename, flown_tablename)

