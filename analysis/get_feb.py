#!/usr/bin/python3.7

# February version of server-side fvf web app script

import os
import sys
import json
import pandas as pd
import datetime
import psycopg2
from sqlalchemy import create_engine

#import elapsed

# ===============================================================

den_artccs = ('ZDV', 'ZLA', 'ZLC', 'ZMP', 'ZKC', 'ZAB', 'ZOA',
              'ZSE', 'ZAU', 'ZID', 'ZME', 'ZFW')

den_artccs = ('ZDV', 'ZKC')
den_artccs = ('ZDV', )

# ===============================================================

cssi_username = os.environ.get('CSSI_USER')
cssi_password = os.environ.get('CSSI_PASSWORD')
cssi_database = os.environ.get('CSSI_DATABASE')
cssi_host     = os.environ.get('CSSI_HOST')

pg_conn = psycopg2.connect( host      = cssi_host,
                            database  = cssi_database,
                            user      = cssi_username,
                            password  = cssi_password)

pg_csr = pg_conn.cursor( )

cssi_engine = create_engine('postgresql://' + \
                   cssi_username + ':' + cssi_password + '@' + \
                   cssi_host + ':5432/' + cssi_database)

# ===============================================================

all_cols = """ acid, fid, corner, dep_apt, flw_dist,
b4_ent_dist, b4_dep_dist, dep_time, arr_time,
flw_geog, b4_ent_geog, b4_dep_geog """

flw_cols = """ acid, fid, corner, dep_apt, flw_dist,
b4_ent_dist, b4_dep_dist, dep_time, arr_time,
flw_geog """

ate_cols = """ acid, fid, corner, b4_ent_geog """

# an fid:   20201211768187
fid_offset= 10000000000000

def retrieve_path_center_geojson(lgr, gdate, ctr, verbose=False):

    #if args.elapsed: aa = elapsed.Elapsed()

    y_m   = gdate.strftime("%Y_%m")
    yhmhd = gdate.strftime("%Y-%m-%d")

    limit = "LIMIT 3" if verbose else ""

    # ============ flown paths
    flown_paths_sql = """
    --  ============ flown paths
  SELECT jsonb_build_object(
    'type',         'Feature',
    'id',           fid,
    'geometry',     ST_AsGeoJSON(flw_geog)::jsonb,
    'properties',   to_jsonb(inputs_flw) - 'flw_geog'
    ) AS feature
  FROM (
    SELECT %s, 'flw' as ptype
    FROM fvf_%s
    WHERE artcc = '%s'
    AND   arr_time >= to_timestamp('%s 00:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    AND   arr_time <  to_timestamp('%s 23:59:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    %s
) inputs_flw """ % ( flw_cols, y_m, ctr, yhmhd, yhmhd, limit )

    # ============ at entry paths
    # need geojson id, but it _must_ be unique
    at_entry_paths_sql = """
    --  ============ at_entry paths
  SELECT jsonb_build_object(
    'type',         'Feature',
    'id',           fidx,
    'geometry',     ST_AsGeoJSON(b4_ent_geog)::jsonb,
    'properties',   to_jsonb(inputs_ate) - 'b4_ent_geog' -'fidx'
    ) AS feature
  FROM (
    SELECT %s, 'ate' as ptype, fid+%d as fidx
    FROM fvf_%s
    WHERE artcc = '%s'
    AND   arr_time >= to_timestamp('%s 00:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    AND   arr_time <  to_timestamp('%s 23:59:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    %s
) inputs_ate """ % ( ate_cols, fid_offset, y_m, ctr, yhmhd, yhmhd, limit )

    # ============ artcc TODO: diff with tracon!!!!!!!

    artcc_sql = """
    -- ============ artcc
  SELECT jsonb_build_object(
    'type',         'Feature',
    'id',           1,  -- watch out for this
    'geometry',     ST_AsGeoJSON(boundary)::jsonb,
    'properties',   to_jsonb(inputs_ctr) - 'boundary'
    ) AS feature
  FROM (
    SELECT *
    FROM centers
    WHERE name='%s'
) inputs_ctr """ % ctr

    # ============  everything together

    sql = """ SELECT jsonb_build_object (
    'type',     'FeatureCollection',
    'features', jsonb_agg(features.feature)
)
FROM (
%s
UNION ALL
%s
UNION ALL
%s
) features; """ % ( flown_paths_sql, at_entry_paths_sql, artcc_sql)

    if verbose: print(sql)
    lgr.debug(sql)

    pg_csr.execute(sql)
    ret = pg_csr.fetchall()
    gjsn = ret[0][0]

    if verbose: print(gjsn)
    lgr.debug(gjsn)

    # ==== for no particular reason, write it out to a file:
    #fn = "py_out_" + ctr + ".gjsn"
    #with open(fn, "w") as fd:
    #    fd.write( json.dumps(gjsn) )
    #print("written:", fn)

    #if args.elapsed: aa.end("retr paths:" + ctr)

    return(gjsn)

# ===========================================================================

# want to do json converstion _later_, but to_dict doesn't know how
# to deal with timestamp, so convert to json and back to dict here :-(

def my_df_to_dict(xxx_df):

    xxx_jsn = xxx_df.to_json(date_format='iso', orient="split",
                                 default_handler=str)
    xxx_dct = json.loads(xxx_jsn)

    return(xxx_dct)

# ===========================================================================

def get_details(lgr, gdate, ctr, verbose=False):

    #if args.elapsed: bb = elapsed.Elapsed()

    y_m   = gdate.strftime("%Y_%m")
    yhmhd = gdate.strftime("%Y-%m-%d")

    sql = """SELECT  acid, fid, corner, artcc, dep_apt, arr_apt,
flw_dist,  b4_ent_dist, b4_dep_dist, dep_time, arr_time
FROM fvf_%s
WHERE artcc = '%s'
-- AND arr_time >= to_timestamp('%s 15:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
-- AND arr_time <  to_timestamp('%s 19:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
""" % (y_m, ctr, yhmhd, yhmhd)

    if verbose: print(sql)
    lgr.debug(sql)

    details_df = pd.read_sql(sql, cssi_engine)

    if verbose: print(details_df)
    lgr.debug(details_df)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # make smaller if testing
    details_df = details_df[2:4] if verbose else details_df

    details_dct = my_df_to_dict( details_df )

    #if args.elapsed: bb.end("retr details:" + ctr)

    return(details_df, details_dct)

# ===========================================================================

def get_chart_from_details(lgr, details_df, ctr):

    #if args.elapsed: cc = elapsed.Elapsed()

    # get the quarter-hour bin for each flight
    # first, make a datetime object out of it
    # FEB: already a datetime???
    #details_df['arr_time_dt'] = details_df['arr_time'].apply(lambda dt:
    #                          datetime.datetime.fromisoformat(dt))

    # second, get the quarter-hour landing time
    details_df['arr_qh'] = details_df['arr_time'].apply(lambda dt:
         datetime.datetime(dt.year, dt.month, dt.day, dt.hour,15*(dt.minute // 15)))

    #details_df = details_df.drop([ 'arr_time_dt', ], axis=1)

    # ---- 3. get corner data for charts

    sch_cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [["b4_dep_dist"]].sum()
    ate_cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [["b4_ent_dist"]].sum()
    flw_cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [["flw_dist"   ]].sum()

    chart_df = pd.merge(sch_cnr_sum_df, ate_cnr_sum_df, on=["arr_qh", "corner"])
    chart_df = pd.merge(chart_df,       flw_cnr_sum_df, on=["arr_qh", "corner"])

    chart_df.reset_index(inplace=True)

    # Q: what are these one for???
    ate_cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [["b4_ent_dist"]].sum()
    flw_cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [["flw_dist" ]].sum()

    lgr.debug("ate_cnr_sum_df")
    #print(ate_cnr_sum_df)
    #print("flw_cnr_sum_df")
    #print(flw_cnr_sum_df)
    #print("chart_df")
    #print(chart_df)

    ate_cnr_sum_df.reset_index(inplace=True)
    flw_cnr_sum_df.reset_index(inplace=True)
    chart_df      .reset_index(inplace=True)

    # NOTE: this will have an index, which we don't have/want/use/need

    ate_cnr_dct = my_df_to_dict( ate_cnr_sum_df )
    flw_cnr_dct = my_df_to_dict( flw_cnr_sum_df )
    chart_dct   = my_df_to_dict( chart_df )

    # print("ate_cnr_dct")
    # pprint(ate_cnr_dct)
    lgr.debug("chart_dct")
    #pprint(chart_dct)

    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    #if args.elapsed: cc.end("form chart:" + ctr)

    return(ate_cnr_dct, flw_cnr_dct, chart_dct)

#############################################################################

def get_postg_data_from_asdidb(lgr, gdate):

    lgr.info("get_postg starting")

    main_output = { 'map_data'     : {},
                    'chart_data'   : {},
                    'details_data' : {} }

    for ctr in den_artccs:

        # -------------- part 1: get map geojson

        map_dct = retrieve_path_center_geojson(lgr, gdate, ctr, args.verbose)

        main_output['map_data'][ctr] = map_dct

        # -------------- part 2: get details

        details_df, details_dct = get_details(lgr, gdate, ctr, args.verbose)

        main_output['details_data'][ctr] = details_dct

        # -------------- part 3: chart details (the MAIN part)

        ate_cnr_dct, flw_cnr_dct, chart_dct = get_chart_from_details(
                                                    lgr, details_df, ctr)

        main_output['chart_data'][ctr] = chart_dct  # AND FLOWN AND CHART???

    lgr.info("get_postg finished")

    # return a dict containing dicts which Flask/CherryPy will json.dumps()
    return(main_output)

#############################################################################
#                            main                                           #
#############################################################################

from pprint import pprint
import argparse
import code

class NotLgr:  # pretend class to let lgr.info() work when not logging
    def info(self, s):
        print(s)
    def debug(self, s):
        if args.verbose: print(s)

#############################################################################

if __name__ == "__main__":

    lgr = NotLgr()   # for non-Connect/Flask ops

    # ==================================================================

    parser = argparse.ArgumentParser(description="this is a very nice program.")

    # for TESTING, use different date:
    parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 10),
            type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='start date yyyy-mm-dd')

    parser.add_argument('-a', '--airport', type=str,
            help="arrival airport", default="DEN")

    parser.add_argument('-v', '--verbose', action='store_const', const=True,
            help="verbosity", default=False )

    parser.add_argument('-o', '--output', type=str,
            help="output style (j=json, p=pretty)", choices=('j', 'p'), default="j")

    #parser.add_argument('-e', '--elapsed', action='store_const', const=True,
    #        help="use elapsed measurements", default=False )

    parser.add_argument('-f', '--filename', type=str,
            help="output filename", default="fixme.json")

    args = parser.parse_args()

    # ==================================================================

    main_output = get_postg_data_from_asdidb(lgr, args.date)

    with open(args.filename, "w") as fd:

        if args.output == 'p':
            fd.write(pprint(main_output))           # nice format

        # actual json-encoded data sent to browser
        if args.output == 'j':
            fd.write(json.dumps(main_output) )

    print("written:", args.filename)
