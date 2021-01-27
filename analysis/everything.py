#!/home/data/local/bin/python3.7

# ############################################################## #
#           NEW: will do BOTH cmd line and flask app             #
# ############################################################## #

import os
import sys
import datetime
import psycopg2
import pandas as pd
import geojson
import socket
import pickle

from shapely.wkt import dumps  #, loads

#==========================================================
# note: d.b. access credentials are in dot files or var panel in Connect

pg_conn = psycopg2.connect(
        host      = os.environ.get('PGHOST'),
        database  = os.environ.get('PGDATABASE'),
        user      = os.environ.get('PGUSER'),
        password  = os.environ.get('PGPASSWORD') )

pg_csr = pg_conn.cursor( )

# ########################################################################## #
#                  the one sql to retrieve everything all at once            #
# ########################################################################## #

def get_everything_from_postgis(lgr, y_m_d, airport, center):

    # artcc / poly to crop (intersection) with

    sql_c = """ WITH C AS
(SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='%s'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='%s')
) as boundary), """  % (center, airport)

    # query_for_first_scheduled (intersection) dist, (intersection) path
    # and metadata of flight

    sql_s = """
SCH AS (SELECT  S.acid, S.flight_index, S.arr_time, S.dep_apt, S.ac_type,
                   path_int_len(S.sched_path, C.boundary) as first_sch_dist,
  ST_AsGeoJSON( ST_Intersection(S.sched_path, C.boundary)) as first_sch_geog
FROM sched_fvf_%s S, C
WHERE arr_apt='%s'
AND   source_type='S'
GROUP BY  S.acid, S.flight_index, S.arr_time, S.dep_apt, S.ac_type,
first_sch_dist, first_sch_geog),
""" % (y_m_d, airport)

    # ================ time of entry into artcc

    sql_e = """E AS (
  SELECT F.acid, F.flight_index,
         lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    C,
    (SELECT * FROM flown_fvf_%s WHERE arr_apt='%s') F
  WHERE intersects(F.flown_path, C.boundary) ), """ % (y_m_d, airport)

    # ================ schedule orig time before time of entry into artcc

    sql_n = """ENTTIME AS (
  SELECT S.flight_index, E.entry_time, max(S.orig_time) as sched_active_at
  FROM E,
       sched_fvf_%s S
  WHERE S.flight_index = E.flight_index
  AND   S.orig_time < E.entry_time
  GROUP BY S.acid, S.flight_index, E.entry_time
), """ % y_m_d

    # ================ sch_at_entry, flown

    sql_a = """
ATENT AS (SELECT  S.flight_index as flight_index_a, F.corner,
                             path_int_len(S.sched_path,  C.boundary)  as at_ent_dist,
             ST_AsGeoJSON(ST_Intersection(S.sched_path,  C.boundary)) as at_ent_geog,
                  path_int_len(trajectory(F.flown_path), C.boundary)  as flown_dist,
  ST_AsGeoJSON(ST_Intersection(trajectory(F.flown_path), C.boundary)) as flown_geog
FROM ENTTIME,
     flown_fvf_%s F,
     sched_fvf_%s S,
     C
WHERE S.flight_index = ENTTIME.flight_index
AND   S.orig_time    = ENTTIME.sched_active_at  -- the important part
AND   F.flight_index = ENTTIME.flight_index) """ %  (y_m_d, y_m_d)

    #  ================ all together

    sql_t = """
SELECT *
FROM SCH, ATENT
WHERE SCH.flight_index = ATENT.flight_index_a"""

    sql = sql_c + sql_s + sql_e + sql_n + sql_a + sql_t

    lgr.info("reading postg")
    lgr.debug(sql)

    evry_df = pd.read_sql(sql, con=pg_conn)

    lgr.debug("postg read completed")

    return(evry_df)

# ######################################################################## #
#                        form GeoJson of all paths                         #
# ######################################################################## #

import json
from geojson import Feature, FeatureCollection
HELPME_OFFSET = 1000000

def form_feature_collection(evry_df, center_feat):

    features = [center_feat, ]

    for index, row in evry_df.iterrows():

        #if index > 5:
        #    break

        # maybe the dropna did this beforehand
        #(str(row['dep_time' ]) == 'NaT') | \
        #    str(row['dep_time' ]),

        if (str(row['arr_time' ]) == 'NaT'):
            print("bad time:", str(row['arr_time' ]))
            continue

        #if (str(row['orig_time']) == 'NaT') |  \
        #   (str(row['arr_time' ]) == 'NaT'):
        #    print("bad time:", str(row['orig_time']), str(row['arr_time' ]))
        #    continue

        # color removed from properties; worked ok
        #"color"    : "magenta",

        # these are items put into GeoJson properties which AppOL will
        # send to DataPos for display in the datablock list

        try:
            pct = "{:.1f}".format( row['flown_dist']*100.0 / row['at_ent_dist'] )
        except:
            pct = "0.0"

        flw_feat = Feature(geometry   = json.loads(row['flown_geog']),
                           id         = row['flight_index'],
                           properties =
                                 { "acid"     : row['acid'],
                                   "flt_ndx"  : row['flight_index'],
                                   "arr_time" : row['arr_time'].isoformat(),
                                   "corner"   : row['corner'],
                                   "dep_apt"  : row['dep_apt'],
                                   "actype"   : row['ac_type'],
                                   "ptype"    : "flw",
                                   "sdist"    : row['first_sch_dist'],
                                   "adist"    : row['at_ent_dist'],
                                   "fdist"    : row['flown_dist'],
                                   "pct"      : pct
                                    })
        features.append(flw_feat)

        # Q: do the rest of these need full properties elements???
        ate_feat = Feature(geometry   = json.loads(row['at_ent_geog']),
                           id         = row['flight_index'] + HELPME_OFFSET,
                           properties = {
                               "acid"     : row['acid'],
                               "flt_ndx"  : row['flight_index'],
                               "arr_time" : row['arr_time'].isoformat(),
                               "ptype"    : "ate",
                               "dist"     : row['at_ent_dist'],
                                     })
        features.append(ate_feat)

        sch_feat = Feature(geometry   = json.loads(row['first_sch_geog']),
                           id         = row['flight_index'] + HELPME_OFFSET*2,
                           properties = {
                               "acid"     : row['acid'],
                               "flt_ndx"  : row['flight_index'],
                               "arr_time" : row['arr_time'].isoformat(),
                               "ptype"    : "sch",
                               "dist"     : row['first_sch_dist'],
                                      })
        features.append(sch_feat)

    feature_collection = FeatureCollection(features)
    return(feature_collection)

    # this gets done later
    #ret_jsn = json.dumps(feature_collection)  # geojson FC structure to string
    #return(ret_jsn)

# ==========================================================================

def get_center_polygon(lgr, center, airport):

    lgr.info("in get_center")
    lgr.info("center:" + center)
    lgr.info("airport:" + airport)

    # ---- x. get ARTCC polygon

    sql_poly = """ SELECT ST_AsGeoJSON(ST_Difference(
    (SELECT boundary::geometry from centers where name='%s'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='%s')
)) """  % (center, airport)

    lgr.info("reading postg")
    lgr.debug(sql_poly)

    pg_csr.execute(sql_poly)
    res = pg_csr.fetchall()

    center_feat = Feature(geometry   = json.loads(res[0][0]),
                          id         = 1,
                          properties = { "name" : center } )

    return(center_feat)

# ######################################################################## #
#                           form data for charts tab                       #
# ######################################################################## #

def form_chart_data(evry_df):

    sch_cnr_sum_df = evry_df.groupby(["arr_hr", "corner"]) [["first_sch_dist"]].sum()
    ate_cnr_sum_df = evry_df.groupby(["arr_hr", "corner"]) [["at_ent_dist"   ]].sum()
    flw_cnr_sum_df = evry_df.groupby(["arr_hr", "corner"]) [["flown_dist"    ]].sum()

    chart_df = pd.merge(sch_cnr_sum_df, ate_cnr_sum_df, on=["arr_hr", "corner"])
    chart_df = pd.merge(chart_df,       flw_cnr_sum_df, on=["arr_hr", "corner"])

    chart_df.reset_index(inplace=True)

    return(chart_df)

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# >>>>> data for the chart Caroline wants
#  done in Python because I don't want to do it in js

def form_flown_at_entry_data(evry_df):

    flw_cnr_sum_df = evry_df.groupby(["arr_hr", "corner"]) [["flown_dist"    ]].sum()

    flw_cnr_sum_df.reset_index(inplace=True)

    flw_pivot_df = flw_cnr_sum_df.pivot(index='arr_hr', columns='corner', values='flown_dist')

    flw_pivot_df.fillna(0, inplace=True)
    flw_pivot_df.reset_index(inplace=True)

    ate_sum_df = evry_df.groupby(["arr_hr",] ) [["at_ent_dist"   ]].sum()

    ate_sum_df.reset_index(inplace=True)

    return(flw_pivot_df, ate_sum_df)

# ######################################################################## #
#                       form data for details table tab                    #
# ######################################################################## #

def form_details(every_df):

    #details_df = every_df.drop([ 'orig_time', 'flight_index_a',
    details_df = every_df.drop([ 'flight_index_a',
                  'first_sch_geog', 'at_ent_geog', 'flown_geog'], axis=1)

    return(details_df)

# ########################################################################### #
# retrieve everything for one day and form json of geogs, charts, and details #
# ########################################################################### #

#pfile = "/home/data/wturner/peverything_small.p"
#pfile = "/tmp/peverything_small.p"
pfile = "/tmp/peverything.p"

def get_everything(lgr, y_m_d, airport, center):


    # ---- 1. get all data from PostGIS (intersection distances and paths)

    everything_df = get_everything_from_postgis(lgr, y_m_d, airport, center)

    # <<<<<<<<<<<<<<<<<< TESTING
    #pickle.dump(everything_df, open( pfile,"wb" ) )
    #everything_df = pickle.load( open( pfile, "rb" ) )

    #args_pickle = False # <<<<<<<<<<<<<<<<<<<< FIXME
    #if args_pickle:
    #    everything_df = pickle.load( open( pfile, "rb" ) )
    #else:
    #    everything_df = get_everything_from_postgis(lgr, y_m_d, airport, center)
    #    pickle.dump(everything_df, open( "peverything_df.p","wb" ) )

    #everything_df = everything_df[:6] # <<<<<<<<<< TESTING

    # <<<<<<<<<<<<<<<<<< TESTING

    # ---------------

    #lgr.info("calling get_center")
    #lgr.info("center:" + center)
    #lgr.info("airport:" + airport)
    center_feat = get_center_polygon(lgr, center, airport)
    #lgr.info("return get_center")
    #lgr.info(center_feat)

    # ---------------

    # ---- 2. form GeoJson of all paths

    fc_gj = form_feature_collection(everything_df, center_feat)

    #lgr.info("fc_gj")
    #lgr.info(fc_gj)

    everything_df['arr_hr'] = everything_df['arr_time'].map(
                                     lambda t: t.strftime("%Y_%m_%d_%H"))

    # ---- 3. get corner data for charts

    chart_df = form_chart_data(everything_df)

    flw_cnr_df, ate_sum_df = form_flown_at_entry_data(everything_df)

    lgr.info(flw_cnr_df)
    lgr.info(ate_sum_df)

    # ---- 4. trim geogs for details table

    details_df = form_details(everything_df)

    # print(details_df)

    # ---- 5. assemble into one massive json

    chart_jn   = json.loads(chart_df.to_json(  date_format='iso', orient="records"))
    flw_cnr_jn = json.loads(flw_cnr_df.to_json(date_format='iso', orient="records"))
    ate_sum_jn = json.loads(ate_sum_df.to_json(date_format='iso', orient="records"))

    details_jn = json.loads(details_df.to_json(date_format='iso', orient="records"))
    #print(type(details_jn))

    every_dict = { 'map_data'       : fc_gj,
                   'chart_data'     : chart_jn,
                   'flw_chart_data' : flw_cnr_jn,
                   'ate_chart_data' : ate_sum_jn,
                   'details_data'   : details_jn }

    return(every_dict)

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
# 'acid', 'flight_index', 'arr_time', 'corner',
#           'first_sch_dist', 'first_sch_geog'
#           'at_ent_dist', 'at_ent_geog'
#           'flown_dist', 'flown_geog'

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

    everything_dict = get_everything(lgr, y_m_d, args.airport, args.center)

    print(json.dumps(everything_dict['flw_chart_data']))
                   #'flw_chart_data' : flw_cnr_jn,
