#!/home/data/local/bin/python3.7

# ############################################################## #
#           NEW: will do BOTH cmd line and flask app             #
# ############################################################## #

import os
import sys
import pytz
import datetime
import psycopg2
import pandas as pd
import geojson
import socket
import pickle

from shapely.wkt import dumps  #, loads
#from shapely.geometry import LineString, mapping, shape

# ------------------------------------------------------------------

go_back = 1    # search back this many minutes
off = 900000   # offset from target id to linestring id

#==========================================================

# HELP: on asdi-db, this runs as a windows Service, i.e. runs under
# windows' python.exe, which I didn't get around to installing geopandas
# (which requires gdal, which requires proj6, which requires gosh knows what)
# So, we do the best we can without geopandas...

# also, need to get postgresql credentials...
# postgresql+psycopg2://user:passwd@asdi-db.cssiinc.com/ciwsdb

# ------------------- rserver  ( production under Flask and RConnect)

if socket.gethostname() == 'acy_test_app_vm_rserver':

    # we're on Linux, under RConnect, with Flask

    # ISSUE: in RConnect deployment: use Settings panel to configure these
    connect_alchemy = "postgresql+psycopg2://"            + \
                    os.environ.get('PGUSER')     + ':' + \
                    os.environ.get('PGPASSWORD') + '@' + \
                    os.environ.get('PGHOST')     + '/' + \
                    os.environ.get('PGDATABASE')

# ------------------- my faa laptop   (local debugging)

if socket.gethostname() == 'JAWAXFL00172839':
    print("this only runs on rserver")
    sys.exit(1)

if socket.gethostname() == 'ASDI-DB':
    print("this only runs on rserver")
    sys.exit(1)

# ------------------- common

# note: d.b. access credentials are in dot files
pg_conn = psycopg2.connect(
        host      = os.environ.get('PGHOST'),
        database  = os.environ.get('PGDATABASE'),
        user      = os.environ.get('PGUSER'),
        password  = os.environ.get('PGPASSWORD') )

pg_csr = pg_conn.cursor( )   # calc_scores needs this


# ########################################################################## #
#                              common sql                                    #
# ########################################################################## #

def crop_poly_sql(arr_apt, center):

    #  ----  C is the artcc polygon to use

    #  Notice: ST_Difference ONLY WORKS ON GEOGRAPHIES!!!!!!!!!!!!!!!!

    #  Issue: I knew making everything a Geography would be a challenge.
    #   1) convert ARTCC boundary to geometry
    #   2) (assuming it is a parent tracon) get the position of the airport and convert to geometry
    #   2a)  Transform that to a 'nice looking' crs, like one of the Lambert Conic Conformal ones
    #   3) make a pretend tracon by making an ST_Buffer around that airport
    #   4) finally, take the ST_Difference of the ARTCC geometry minus the tracon buffer geometry
    #   6) cast it back to a Geography (is this needed???)

    sqlc = """
WITH C AS
(SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='%s'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='%s')
) as boundary) """ % (center, arr_apt)

    return(sqlc)

    # ----  E and J for 4) active at artcc entry ++++++

def common_sql_4(arr_apt, center, y_m_d):

    #  ---- E is the SELECTion of acid, flight_index, and ZDV entry time of each flight

    sqle = """
E AS (
  SELECT F.acid, F.flight_index,
         lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    C,
    (SELECT * FROM flown_fvf_%s WHERE arr_apt='%s') F
  WHERE intersects(F.flown_path, C.boundary) ),
  """ % ( y_m_d, arr_apt)

    #  ---- J is the SELECTion of the scheduled path previous to artcc entry time

    sqlj = """
J AS (
  SELECT S.acid, S.flight_index, E.entry_time, max(S.orig_time) as sched_active_at
  FROM E,
       sched_fvf_%s S
  WHERE S.flight_index = E.flight_index
  AND   S.orig_time < E.entry_time
  GROUP BY S.acid, S.flight_index, E.entry_time
) """ % y_m_d

    return (sqle, sqlj)

# ########################################################################## #
#                              GeoJson                                       #
# ########################################################################## #

def query_one_corner_flights_as_geojson(lgr, arr_apt, center, corner, y_m_d):

    sqlc = crop_poly_sql(arr_apt, center)
    sqle, sqlj = common_sql_4(arr_apt, center, y_m_d)

    # >>>>>>>>>>>>> do this if GeoJson:
    sql_fc = """
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(feature)
    )
FROM (
  SELECT jsonb_build_object(
    'type',       'Feature',
    'id',         gid,
    'geometry',   ST_AsGeoJSON(geom)::jsonb,
    'properties', to_jsonb(inputs) - 'gid' - 'geom'
  ) AS feature
  FROM (
  -- ===========================
  -- ==== sched part
( SELECT  'green' as color, F.acid, F.flight_index as gid, ST_Intersection(S.sched_path, C.boundary) as geom
FROM J,
     flown_fvf_%s F,
     sched_fvf_%s S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
AND   F.corner = '%s'
) UNION ALL (
  -- ==== flown part
SELECT  'blue' as color, F.acid, F.flight_index+1000000 as gid, ST_Intersection(trajectory(F.flown_path), C.boundary) as geom
FROM J,
     flown_fvf_%s F,
     sched_fvf_%s S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
AND   F.corner = '%s'
) UNION ALL (
SELECT '#ffb366' as color, '%s' as acid, 1 as gid, boundary as geom
FROM C
)
  -- ===========================
  ) inputs
) features """ % ( y_m_d, y_m_d, corner, y_m_d, y_m_d, corner, center)

    sql = sqlc + sqle + sqlj + sql_fc

    lgr.info("reading postg")
    lgr.debug(sql)

    pg_csr.execute(sql)
    res = pg_csr.fetchall()
    lgr.debug(res)

    data_gj = res[0][0]

    return(data_gj)

# ########################################################################## #
#                              Table                                         #
# ########################################################################## #

def query_all_corners_flights_as_table(lgr, arr_apt, center, y_m_d):

    sqlc = crop_poly_sql(arr_apt, center)
    sqle, sqlj = common_sql_4(arr_apt, center, y_m_d)

    sql_table = """ SELECT  S.acid, F.corner, S.flight_index, S.arr_time,
  path_int_len(S.sched_path, C.boundary) as at_entry_dist,
  path_int_len(trajectory(F.flown_path), C.boundary) as flown_dist,
  path_int_diff_pct( trajectory(f.flown_path), S.sched_path, C.boundary) as pct
FROM J,
     flown_fvf_%s F,
     sched_fvf_%s S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
ORDER BY F.corner, pct""" % (y_m_d, y_m_d)

    sql = sqlc + ',' + sqle + sqlj + sql_table

    lgr.info("reading postg")
    lgr.debug(sql)

    all_flts_df = pd.read_sql(sql, con=pg_conn)
    return(all_flts_df)


# ######################################################################## #
#                           turn tabular into summary                      #
# ######################################################################## #

def summarize_by_corner(all_flts_df):  # UNUSED

    # ----  just testing, are these useful???

    sch_cnr_sum_df = all_flts_df.groupby(["corner"]) [["sched_dist"]].sum()
    flw_cnr_sum_df = all_flts_df.groupby(["corner"]) [["flown_dist"]].sum()

    print("sched:")
    print(sch_cnr_sum_df)
    print("flown:")
    print(flw_cnr_sum_df)

    together_df = pd.merge(sch_cnr_sum_df, flw_cnr_sum_df, on="corner")
    print("together:")
    print(together_df)

# ------------------------------------------------------------------------

def summarize_by_hour(lgr, airport, center, y_m_d):

    all_flts_df = query_all_corners_flights_as_table(lgr, airport,
                                                         center, y_m_d)
    # ---- summarize by hour

    all_flts_df['hour'] = all_flts_df['arr_time'].apply(lambda dt:
               datetime.datetime( dt.year, dt.month, dt.day, dt.hour,0,0,0))

    # sch_hr_sum_df = all_flts_df.groupby(["corner","hour"]) [["sched_dist"]].sum()
    # flw_hr_sum_df = all_flts_df.groupby(["corner","hour"]) [["flown_dist"]].sum()

    # no difference:
    sch_hr_sum_df = all_flts_df.groupby(["corner","hour"]).agg( {"sched_dist":'sum'})
    flw_hr_sum_df = all_flts_df.groupby(["corner","hour"]).agg( {"flown_dist":'sum'})

    hourly_df = pd.merge(sch_hr_sum_df, flw_hr_sum_df, on=["corner","hour"]).reset_index()

    #hourly_df.to_csv(hrly_fn, index=False)

    # ---- now return pandas dataframe as json

    hourly_js = hourly_df.to_json(date_format='iso', orient="records")

    #print("+++++++ after to_json")
    #print(hourly_js)  # print has dbl quotes

    #print("+++++++ after loads")
    #parsed_js = json.loads(hourly_js)

    return(hourly_js)

# ######################################################################## #
#                               Paths                                      #
# ######################################################################## #

# ---- Path.1

def query_for_first_scheduled( airport, center, y_m_d):

    sqlc = crop_poly_sql(airport, center)

    sql_p1 = """ SELECT  S.acid, S.flight_index, S.arr_time, min(orig_time) as orig_time,
  path_int_len(S.sched_path, C.boundary) as first_sch_dist
FROM sched_fvf_%s S, C
WHERE arr_apt='%s'
AND   source_type='S'
GROUP BY  S.acid, S.flight_index, S.arr_time, first_sch_dist ;
""" % (y_m_d, airport)

    sql = sqlc + sql_p1

    lgr.info("reading postg")
    lgr.debug(sql)

    p1_df = pd.read_sql(sql, con=pg_conn)
    return(p1_df)

# -- ============================= PATH.2 ; first filed
# ---- Path.2
# -- (first one of the) First Filed

def query_for_first_filed( airport, center, y_m_d):

    sqlc = crop_poly_sql(airport, center)

    # -- use FF on row number to make sure there's only one
    sql_p2 = """
FF AS (
  SELECT * FROM (
    SELECT *,
    row_number() OVER (PARTITION BY flight_index ORDER BY orig_time DESC) AS ROW_NUMBER
    FROM sched_fvf_%s
    WHERE arr_apt='%s'
    AND   source_type='F'
  ) as foo WHERE ROW_NUMBER = 1 )

SELECT  FF.acid, FF.flight_index, FF.arr_time, FF.orig_time,
  path_int_len(FF.sched_path, C.boundary) as first_filed_dist
FROM FF, C ;""" % (y_m_d, airport)

    sql = sqlc + ',' + sql_p2

    lgr.info("reading postg")
    lgr.debug(sql)

    p2_df = pd.read_sql(sql, con=pg_conn)
    return(p2_df)

# -- ============================= PATH.3 ; at departure
# -- at departure

def query_for_active_at_dep( airport, center, y_m_d):

    sqlc = crop_poly_sql(airport, center)

    sql_p3 = """
AD AS (
  SELECT * FROM (
    SELECT *,
    row_number() OVER (PARTITION BY flight_index ORDER BY orig_time DESC) AS ROW_NUMBER
    FROM sched_fvf_%s
    WHERE arr_apt='%s'
    AND   orig_time < dep_time
  ) as foo WHERE ROW_NUMBER = 1 )

SELECT  AD.acid, AD.flight_index, AD.arr_time, AD.orig_time,
  path_int_len(AD.sched_path, C.boundary) as before_dep_dist
FROM AD, C ;""" % (y_m_d, airport)

    sql = sqlc + ',' + sql_p3

    lgr.info("reading postg")
    lgr.debug(sql)

    p2_df = pd.read_sql(sql, con=pg_conn)
    return(p2_df)


# ######################################################################## #
#                              standalone main                             #
# ######################################################################## #

import json
from pprint import pprint

class NotLgr:  # pretend class to let lgr.info() work when not logging
    def info(self, s):
        print(s)
    def debug(self, s):
        if args.verbose: print(s)

# ==========================================================================

import argparse

if __name__ == "__main__":

    # ################################################################### #
    #                           argparse                                  #
    # ################################################################### #

    parser = argparse.ArgumentParser(description="a very good program")

    parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 10),
                type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                        help='start date yyyy-mm-dd')

    parser.add_argument('-a', '--airport', type=str,
                help="arrival airport", default="DEN")

    parser.add_argument('-z', '--center', type=str,   # abbr. is non-standard
                help="center to transit", default="ZDV")

    parser.add_argument('-c', '--corner', type=str,
                help="corner post", default="ne",
                choices=('ne', 'se', 'sw', 'nw') )

    parser.add_argument('-v', '--verbose', action='store_const', const=True,
                help="verbosity", default=False )

    parser.add_argument('-p', '--pickle', action='store_const', const=True,
                help="use pickle instead of oracle", default=False )

    parser.add_argument('-f', '--function', type=str,
                help="function to run", default="1",
                choices=('1', '2', '3', '4') )

    args = parser.parse_args()

    # ####################################################################### #
    # ---- and adjust args to be in a nice format

    # filename of csv file (containing airport and operational day)
    csv_fn = args.airport.lower() + '_' + args.date.strftime("%Y_%m_%d") + ".csv"
    hrly_fn = args.airport.lower() + '_' + args.date.strftime("%Y_%m_%d") + "_hourly.csv"

    y_m_d    = args.date.strftime("%Y_%m_%d")

    # ####################################################################### #

    lgr = NotLgr()
    #print("hello sailor")

    # ---- 1. retrieve tabular data of acid, corner, arr time, both distances

    if args.function == '1':

        if args.pickle:
            all_flts_df = pickle.load( open( "all_flts_df.p", "rb" ) )
        else:
            all_flts_df = query_all_corners_flights_as_table(lgr, args.airport,
                                                         args.center, y_m_d)
            pickle.dump(all_flts_df, open( "all_flts_df.p","wb" ) )

        with pd.option_context('display.max_rows', None,
                               'display.max_columns', None,
                               'display.width', 299,
                               ):
            print(all_flts_df)

        all_flts_df.to_csv(csv_fn, index=False)

    # ---- 2. analyze corners and return as json

    if args.function == '2':

        hourly_js = summarize_by_hour(lgr, args.airport, args.center, y_m_d)

        print(hourly_js)   # print has single quotes

        #print("+++++++ after dumps")
        #print(json.dumps(parsed_js, indent=4))  # prettified
        #print(">>>>>>>")

    # ---- 3. call query as if were a flask call

    if args.function == '3':

        fc = query_one_corner_flights_as_geojson(lgr, args.airport,
                                    args.center, args.corner, y_m_d)
        print("+++++++")
        print(json.dumps(fc))
        print(">>>>>>>")
        pprint(fc)

    # ----
    # ---- Path.1 (first) scheduled
    # ---- Path.2 first filed
    # ---- Path.3 active at departure
    # ---- Path.4 active at artcc entry
    # ---- Path.5 flown
    # ----

    # ---- 4. NEW: query for  Path.1

    if args.function == '4':

        p1_df = query_for_first_scheduled( args.airport, args.center, y_m_d)
        p1_df.drop(['arr_time', 'orig_time'], axis=1, inplace=True)
        print("p1_df")
        print(p1_df)

        p2_df = query_for_first_filed( args.airport, args.center, y_m_d)
        p2_df.drop(['arr_time', 'orig_time'], axis=1, inplace=True)
        print("p2_df")
        print(p2_df)

        p12_df = pd.merge(p1_df, p2_df, on='flight_index')
        p12_df.drop(['acid_y'], axis=1, inplace=True)
        print("p12_df")
        print(p12_df)

        p3_df = query_for_active_at_dep( args.airport, args.center, y_m_d)
        p3_df.drop(['arr_time', 'orig_time'], axis=1, inplace=True)
        print("p3_df")
        print(p3_df)

        p123_df = pd.merge(p12_df, p3_df, on='flight_index')
        p123_df.drop(['acid_x'], axis=1, inplace=True)
        print("p123_df")
        print(p123_df)

        # +++++++++++ from above:
        if args.pickle:
            p45_df = pickle.load( open( "p45_df.p", "rb" ) )
        else:
            p45_df = query_all_corners_flights_as_table(lgr, args.airport,
                                                         args.center, y_m_d)
            pickle.dump(p45_df, open( "p45_df.p","wb" ) )

        print("p45_df")
        print(p45_df)
        #print(p45_df.columns)

        p12345_df = pd.merge(p123_df, p45_df, on='flight_index')
        #print("a", p12345_df.columns)
        p12345_df.drop(['acid_y'], axis=1, inplace=True)
        #print("b", p12345_df.columns)
        #p12345_df.rename( {'acid_x' : 'acid'}, inplace=True)
        #print("c", p12345_df.columns)

        p12345_df = p12345_df[[ 'acid_x', 'flight_index', 'corner',
            'arr_time',
            'first_sch_dist', 'first_filed_dist', 'before_dep_dist',
            'at_entry_dist', 'flown_dist', 'pct' ]]

        #print("p12345_df")
        #print(p12345_df)

        with pd.option_context('display.max_rows', None,
                               'display.max_columns', None,
                               'display.width', 299,
                               ):
            print(p12345_df)

        p12345_df.to_csv(csv_fn, index=False)

