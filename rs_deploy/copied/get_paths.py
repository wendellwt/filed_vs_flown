#!/usr/bin/python3.7

# ############################################################## #
#           web server postgis retrieval procedures              #
# ############################################################## #

# imported from either SwimService.py or app.py
# to perform queries to PostGIS on asdi-db

# -------------------------------------------------------
# to run on asdi-db using the server's python:
#   /cygdrive/c/Users/wturner/Python37/python.exe get_tracks.py

# to run on faa laptop:
#  /usr/bin/python3.7 get_tracks.py

# to run on rserver:
#  python3.7 get_tracks.py
# -------------------------------------------------------------------------
# ISSUE: it was too hard to install GeoPandas (and GEOS and Proj and ...)
# on the Windows Python (cygwin python was fine).  Also, it was better
# to have just one set of procedures (rather than a GeoPandas (rserver)
# one and a Python/Sahpely one (asdi-db)
# -------------------------------------------------------------------------

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

    connect_alchemy = "postgresql+psycopg2://"            + \
                    os.environ.get('PGUSER')     + ':' + \
                    os.environ.get('PGPASSWORD') + '@' + \
                    os.environ.get('PGHOST')     + '/' + \
                    os.environ.get('PGDATABASE')

# ------------------- asdi-db    (production under CherryPy)

if socket.gethostname() == 'ASDI-DB':

    # we're on Windows, under Service, with CherryPy

    conf_file = os.path.dirname(os.path.realpath(__file__)) + \
                                 os.path.sep + '.winsvc.toml'

    # $ /cygdrive/c/Users/wturner/Python37/python.exe -m pip install toml
    import toml

    with open(conf_file) as fd:
        raw_config = fd.read()
    cfg = toml.loads(raw_config)

    # ISSUE: on asdi-db: use .winsvc.toml config file
    connect_alchemy = "postgresql+psycopg2://"            + \
                         cfg['CSSI_USER']     + ':' + \
                         cfg['CSSI_PASSWORD'] + '@' + \
                         cfg['CSSI_HOST']     + '/' + \
                         cfg['CSSI_DATABASE']

# ------------------- common

# note: d.b. access credentials are in dot files
pg_conn = psycopg2.connect(
        host      = os.environ.get('PGHOST'),
        database  = os.environ.get('PGDATABASE'),
        user      = os.environ.get('PGUSER'),
        password  = os.environ.get('PGPASSWORD') )

pg_csr = pg_conn.cursor( )   # calc_scores needs this

# WAY more trouble than it's worth: engine = create_engine(connect_alchemy)

# ########################################################################## #
#                              new fvf                                          #
# ########################################################################## #

def query_fvf(lgr, unk):

    # =========================================================
    # using TEMPORARY table to 'join' 'union' 'whatever'
    # WORKS FINE!!!

    sqlc = """
--
-- ============== C is the artcc polygon to use
-- Notice: ST_Difference ONLY WORKS ON GEOGRAPHIES!!!!!!!!!!!!!!!!

-- Issue: I knew making everything a Geography would be a challenge.
--  1) convert ARTCC boundary to geometry
--  2) (assuming it is a parent tracon) get the position of the airport and convert to geometry
--  2a)  Transform that to a 'nice looking' crs, like one of the Lambert Conic Conformal ones
--  3) make a pretend tracon by making an ST_Buffer around that airport
--  4) finally, take the ST_Difference of the ARTCC geometry minus the tracon buffer geometry
--  6) cast it back to a Geography (is this needed???)

WITH C AS
(SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='%s'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='%s')
) as boundary), """ % ('ZDV', 'DEN')


    sqle = """
--
-- ============== E is the SELECTion of acid, flight_index, and ZDV entry time of each flight
--
E AS (
  SELECT F.acid, F.flight_index,
         lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    C,
    (SELECT * FROM flown_fvf_%s WHERE arr_apt='%s') F
  WHERE intersects(F.flown_path, C.boundary) ),
  """ % ( '2020_01_10', 'DEN')

    sqlj = """
--
-- ============== J is the SELECTion of the scheduled path previous to artcc entry time
--
J AS (
  SELECT S.acid, S.flight_index, E.entry_time, max(S.orig_time) as sched_active_at
  FROM E,
       sched_fvf_%s S
  WHERE S.flight_index = E.flight_index
  AND   S.orig_time < E.entry_time
  GROUP BY S.acid, S.flight_index, E.entry_time
) """ % ('2020_01_10', )

    sql_fc = """
--
--
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
) features """ % ( '2020_01_10', '2020_01_10', 'ne', '2020_01_10', '2020_01_10', 'ne', 'ZDV')

    sql = sqlc + sqle + sqlj + sql_fc

    lgr.info("reading postg")
    lgr.debug(sql)

    pg_csr.execute(sql)
    res = pg_csr.fetchall()
    lgr.debug(res)

    data_gj = res[0][0]

    return(data_gj)

# ########################################################################## #
#                              ????                                          #
# ########################################################################## #

def query_all(lgr, unk):

    # =========================================================
    # using TEMPORARY table to 'join' 'union' 'whatever'
    # WORKS FINE!!!

    sql = """
-- first part:

DROP TABLE IF EXISTS fdxs_to_use;

-- second part:

SELECT DISTINCT flight_index INTO TEMPORARY TABLE fdxs_to_use
  FROM sched_fvf_2019_06_22
  WHERE dep_apt='CLT' AND arr_apt='ORD'
  LIMIT 5;  -- SO response will fit on page

-- third part:

SELECT jsonb_build_object(
    'type',     'FeatureCollection',
    'features', jsonb_agg(features.feature)
)
FROM (
  SELECT jsonb_build_object(
    'type',       'Feature',
    'geometry',   ST_AsGeoJSON(trajectory(flown_path))::jsonb,
    'properties', to_jsonb(inputs) - 'flown_path'
  ) AS feature
  FROM (SELECT 'magenta' color, *
        FROM flown_fvf_2019_06_22
        WHERE flight_index IN (SELECT flight_index FROM fdxs_to_use)
       ) inputs
  UNION
  SELECT jsonb_build_object(
    'type',       'Feature',
    'geometry',   ST_AsGeoJSON(sched_path)::jsonb,
    'properties', to_jsonb(inputs) - 'sched_path' - 'waypoints'
  ) AS feature
  FROM (SELECT 'green' color, *
        FROM sched_fvf_2019_06_22
        WHERE flight_index IN (SELECT flight_index FROM fdxs_to_use)
       ) inputs
  ) features;
 """

    lgr.info("reading postg")
    lgr.debug(sql)

    pg_csr.execute(sql)
    res = pg_csr.fetchall()
    lgr.debug(res)

    data_gj = res[0][0]

    return(data_gj)

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

    fc = query_fvf( lgr, "KIAD" )

    print("+++++++")
    print(json.dumps(fc))
    print(">>>>>>>")
    pprint(fc)

