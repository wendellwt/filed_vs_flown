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

from sqlalchemy import create_engine
from shapely.wkt import dumps, loads
from shapely.geometry import LineString, mapping, shape

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

def common_sql(arr_apt, center, y_m_d):

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
) as boundary), """ % (center, arr_apt)


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

    return (sqlc, sqle, sqlj)

# ########################################################################## #
#                              GeoJson                                       #
# ########################################################################## #

def query_one_corner_flights_as_geojson(lgr, arr_apt, center, corner, y_m_d):

    sqlc, sqle, sqlj = common_sql(arr_apt, center, y_m_d)

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

    sqlc, sqle, sqlj = common_sql(arr_apt, center, y_m_d)

    sql_table = """ SELECT  S.acid, F.corner, S.flight_index, S.arr_time,
  path_int_len(S.sched_path, C.boundary) as sched_dist_%s,
  path_int_len(trajectory(F.flown_path), C.boundary) as flown_dist_%s,
  path_int_diff_pct( trajectory(f.flown_path), S.sched_path, C.boundary) as pct
FROM J,
     flown_fvf_%s F,
     sched_fvf_%s S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
ORDER BY F.corner, pct""" % (corner, corner, y_m_d, y_m_d)

    sql = sqlc + sqle + sqlj + sql_table

    lgr.info("reading postg")
    lgr.debug(sql)

    all_flts_df = pd.read_sql(sql, con=pg_conn)

    print(all_flts_df)
    all_flts_df.to_csv("atest.csv", index=False)

    #pg_csr.execute(sql)
    #for res in pg_csr.fetchall():
    #    print(res)

    sys.exit(1)

# ######################################################################## #
#                              standalone main                             #
# ######################################################################## #

import json
from pprint import pprint

class NotLgr:  # pretend class to let lgr.info() work when not logging
    def info(self, s):
        print(s)
    def debug(self, s):
        print(s)

# ==========================================================================

if __name__ == "__main__":

    lgr = NotLgr()
    print("hello sailor")

    # get these from args: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    y_m_d = "2020_01_10"
    arr_apt = 'DEN'
    center = 'ZDV'
    corner = 'ne'

    tbl = query_all_corners_flights_as_table(lgr, arr_apt, center, y_m_d)

    # fc = query_one_corner_flights_as_geojson(lgr, arr_apt, center, corner, y_m_d)
    # print("+++++++")
    # print(json.dumps(fc))
    # print(">>>>>>>")
    # pprint(fc)

