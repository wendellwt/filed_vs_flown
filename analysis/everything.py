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

#==========================================================

if socket.gethostname() == 'acy_test_app_vm_rserver':

    # we're on Linux, under RConnect, with Flask

    # ISSUE: in RConnect deployment: use Settings panel to configure these
    connect_alchemy = "postgresql+psycopg2://"            + \
                    os.environ.get('PGUSER')     + ':' + \
                    os.environ.get('PGPASSWORD') + '@' + \
                    os.environ.get('PGHOST')     + '/' + \
                    os.environ.get('PGDATABASE')

# ------------------- common

# note: d.b. access credentials are in dot files
pg_conn = psycopg2.connect(
        host      = os.environ.get('PGHOST'),
        database  = os.environ.get('PGDATABASE'),
        user      = os.environ.get('PGUSER'),
        password  = os.environ.get('PGPASSWORD') )

pg_csr = pg_conn.cursor( )

# ########################################################################## #
#                              common sql                                    #
# ########################################################################## #

def get_everything(lgr):
    sql = """ WITH C AS
(SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='ZDV'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='DEN')
) as boundary),

-- query_for_first_scheduled (meta, (intersection) dist, (intersection) path

SCH AS (SELECT  S.acid, S.flight_index, S.arr_time, min(orig_time) as orig_time,
                   path_int_len(S.sched_path, C.boundary) as first_sch_dist,
  ST_AsGeoJSON( ST_Intersection(S.sched_path, C.boundary)) as first_sch_geom
FROM sched_fvf_2020_01_10 S, C
WHERE arr_apt='DEN'
AND   source_type='S'
GROUP BY  S.acid, S.flight_index, S.arr_time, first_sch_dist, first_sch_geom),

-- ================ time of entry into artcc

E AS (
  SELECT F.acid, F.flight_index,
         lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    C,
    (SELECT * FROM flown_fvf_2020_01_10 WHERE arr_apt='DEN') F
  WHERE intersects(F.flown_path, C.boundary) ),

-- ================ schedule orig time before time of entry into artcc

ENTTIME AS (
  SELECT S.flight_index, E.entry_time, max(S.orig_time) as sched_active_at
  FROM E,
       sched_fvf_2020_01_10 S
  WHERE S.flight_index = E.flight_index
  AND   S.orig_time < E.entry_time
  GROUP BY S.acid, S.flight_index, E.entry_time
),

-- ================ sch_at_entry, flown

ATENT AS (SELECT  S.flight_index as flight_index_a, F.corner,
                             path_int_len(S.sched_path,  C.boundary)  as at_ent_dist,
             ST_AsGeoJSON(ST_Intersection(S.sched_path,  C.boundary)) as at_ent_geom,
                  path_int_len(trajectory(F.flown_path), C.boundary)  as flown_dist,
  ST_AsGeoJSON(ST_Intersection(trajectory(F.flown_path), C.boundary)) as flown_geom
FROM ENTTIME,
     flown_fvf_2020_01_10 F,
     sched_fvf_2020_01_10 S,
     C
WHERE S.flight_index = ENTTIME.flight_index
AND   S.orig_time    = ENTTIME.sched_active_at  -- the important part
AND   F.flight_index = ENTTIME.flight_index)

-- ================ all together

-- SELECT sch.acid, sch.flight_index, sch.arr_time, sch.orig_time, sch.first_sch_dist, sch.first_sch_geom,
        -- atent.corner, atent.at_ent_dist, atent.at_ent_geom, atent.flown_dist, atent.flown_geom
SELECT *
FROM SCH, ATENT
WHERE SCH.flight_index = ATENT.flight_index_a"""

    lgr.info("reading postg")
    lgr.debug(sql)

    everything_df = pd.read_sql(sql, con=pg_conn)
    return(everything_df)

# ######################################################################## #
#                        form GeoJson of all paths                         #
# ######################################################################## #

import json
from geojson import Feature, FeatureCollection

def form_feature_collection(everything_df):

    features = []
    #bad = 0

    for index, row in everything_df.iterrows():

        #if index > 5:
        #    break

        # maybe the dropna did this beforehand
        #(str(row['dep_time' ]) == 'NaT') | \
        #    str(row['dep_time' ]),

        if (str(row['orig_time']) == 'NaT') |  \
           (str(row['arr_time' ]) == 'NaT'):
            print("bad time:", str(row['orig_time']), str(row['arr_time' ]))
            #bad += 1
            continue

        flw_feat = Feature(geometry = json.loads(row['flown_geom']),
                    properties = { "acid"     : row['acid'],
                                   "flt_ndx"  : row['flight_index'],
                                   "arr_time" : row['arr_time'].isoformat(),
                                   "corner"   : row['corner'],
                                   "ptype"    : "flw",
                                   "color"    : "magenta",
                                   "dist"     : row['flown_dist'],
                                    })
        features.append(flw_feat)

        ate_feat = Feature(geometry = json.loads(row['at_ent_geom']),
                    properties = { "acid"     : row['acid'],
                                   "flt_ndx"  : row['flight_index'],
                                   "arr_time" : row['arr_time'].isoformat(),
                                   "corner"   : row['corner'],
                                   "ptype"    : "ate",
                                   "color"    : "blue",
                                   "dist"     : row['at_ent_dist'],
                                    })
        features.append(ate_feat)

        sch_feat = Feature(geometry = json.loads(row['first_sch_geom']),
                    properties = { "acid"     : row['acid'],
                                   "flt_ndx"  : row['flight_index'],
                                   "arr_time" : row['arr_time'].isoformat(),
                                   "corner"   : row['corner'],
                                   "ptype"    : "sch",
                                   "color"    : "green",
                                   "dist"     : row['first_sch_dist'],
                                    })
        features.append(sch_feat)

    feature_collection = FeatureCollection(features)

    ret_jsn = json.dumps(feature_collection)  # geojson FC structure to string

    return(ret_jsn)

# ######################################################################## #
#                              standalone main                             #
# ######################################################################## #

from pprint import pprint

class NotLgr:  # pretend class to let lgr.info() work when not logging
    def info(self, s):
        print(s)
    def debug(self, s):
        if args.verbose: print(s)

# ==========================================================================

import argparse

if __name__ == "__main__":

    lgr = NotLgr()   # for non-Connect/Flask ops

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

    parser.add_argument('-v', '--verbose', action='store_const', const=True,
                help="verbosity", default=False )

    parser.add_argument('-p', '--pickle', action='store_const', const=True,
                help="use pickle instead of oracle", default=False )

    args = parser.parse_args()

    # ======================================================================

    y_m_d    = args.date.strftime("%Y_%m_%d")

    # ####################################################################### #

    # ---- 1. get all data from PostGIS (intersection distances and paths)

    if args.pickle:
        everything_df = pickle.load( open( "peverything_df.p", "rb" ) )
    else:
        everything_df = get_everything(lgr)
        pickle.dump(everything_df, open( "peverything_df.p","wb" ) )

    # [762 rows x 12 columns]
    # Index(['acid', 'flight_index', 'arr_time', 'orig_time', 'first_sch_dist',
    #    'first_sch_geom', 'flight_index_a', 'corner', 'at_ent_dist',
    #    'at_ent_geom', 'flown_dist', 'flown_geom'],

    # ---- 2. form GeoJson of all paths

    fc = form_feature_collection(everything_df)

    print(fc)
