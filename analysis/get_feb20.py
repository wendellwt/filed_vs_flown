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

args_verbose = False

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

def get_distances_for_path(path):

    if path == "upto":
        return """
scheduled_upto_dist     as sch_dist,
first_filed_upto_dist   as fld_dist,
last_filed_upto_dist    as dep_dist,
flown_upto_dist         as flw_dist,
0 as ent_dist """

    else:  # path = within or full

        return """
scheduled_within_dist   as sch_dist,
first_filed_within_dist as fld_dist,
last_filed_within_dist  as dep_dist,
flown_within_dist       as flw_dist,
at_entry_within_dist    as ent_dist """

src_to_col = {
        "sched"  : "scheduled",
        "filed"  : "first_filed",
        "depart" : "last_filed",
        "at_ent" : "at_entry",
        "flown"  : "flown" }

# -----------------------------------------------------------------

all_cols = """ acid, fid, corner, dep_apt, flw_dist,
b4_ent_dist, b4_dep_dist, dep_time, arr_time,
flw_geog, b4_ent_geog, b4_dep_geog """

flw_cols = """ acid, fid, corner, dep_apt, ac_type, flw_dist,
b4_ent_dist, b4_dep_dist, dep_time, arr_time,
flw_geog """

# arr_time is used in OL.vue to display hourly!!!
ate_cols = """ acid, fid, corner, arr_time, b4_ent_geog """

# an fid:   20201211768187
fid_offset= 10000000000000

def retrieve_path_center_geojson_f20(lgr, gdate, ctr, path, source, verbose=False):

    lgr.info("retrieve_path_center starting")
    #if args.elapsed: aa = elapsed.Elapsed()

    y_m   = gdate.strftime("%Y_%m")
    yhmhd = gdate.strftime("%Y-%m-%d")

    # tomorrow : FIXME -- month wrap-around needs JOIN on next table!!!
    # tomorrow : FIXME -- month wrap-around needs JOIN on next table!!!

    yhmhd_tom = (gdate + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    limit = "LIMIT 3" if verbose else ""

    # ============ flown paths
    # gdate  : ok
    # ctr    : ok, even if zzz, right?
    # path   : ok
    # source : needs dict:

    if path != 'full':
        geo_col = "%s_%s_geog" % (src_to_col[source], path)
        use_ctr = ctr
    else:
        # if ctr = ZZZ then path MUST be within (right?)
        geo_col = "%s_within_geog" % src_to_col[source]
        use_ctr = 'ZZZ'

    # and get all distances for no particular reason...

    distances = get_distances_for_path(path)

    # ============ flown paths

    paths_sql = """
    --  ============ flown paths
  SELECT jsonb_build_object(
    'type',         'Feature',
    'id',           fid,
    'geometry',     ST_AsGeoJSON(%s)::jsonb,
    'properties',   to_jsonb(inputs_flw) - '%s'
    ) AS feature
  FROM (
  SELECT acid, fid, dep_apt, arr_time, corner, ac_type, %s, %s
    FROM fvfb_%s
    WHERE artcc = '%s'
    AND   arr_time >= to_timestamp('%s 08:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    AND   arr_time <  to_timestamp('%s 08:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
    %s
) inputs_flw """ % ( geo_col, geo_col, distances, geo_col, y_m, use_ctr, yhmhd, yhmhd_tom, limit )

    artcc_sql = get_artcc_sql(ctr, path, source)

    # ============  everything together

    # WARNING: pd.read_sql fixes timezones for us, plain SELECT does NOT!!!
    sql = """SET TIME ZONE 'UTC';
    SELECT jsonb_build_object (
    'type',     'FeatureCollection',
    'features', jsonb_agg(features.feature)
)
FROM (
%s
UNION ALL
%s
) features; """ % ( paths_sql, artcc_sql)

    #print(sql)
    #lgr.debug(sql)
    #lgr.info(sql)

    lgr.info("calling .execute()")

    pg_csr.execute(sql)

    ret = pg_csr.fetchall()

    gjsn = ret[0][0]

    #if verbose: print(gjsn)
    #lgr.debug(gjsn)
    lgr.info("got response")

    # ==== for no particular reason, write it out to a file:
    #fn = "py_out_" + ctr + ".gjsn"
    #with open(fn, "w") as fd:
    #    fd.write( json.dumps(gjsn) )
    #print("written:", fn)

    #if args.elapsed: aa.end("retr paths:" + ctr)

    return(gjsn)

# ===========================================================================

# ============ artcc
# note: no properties, boundary only
# note: if path = full   : tracon
#       if path = within : center - tracon
#       if path = upto   : exteriorRing of tiers

tier_1 = [ "ZLA", "ZLC", "ZMP", "ZKC", "ZAB",]

def get_artcc_sql(ctr, path, source):

    # print("get_artcc_sql:", ctr, path, source)

    # ============== tracon only  FIXME: 'DEN'

    if path == "full":

        inner_artcc_sql = """
    SELECT ST_Transform(ST_Transform(boundary::geometry,26754),4326) as boundary
      FROM tracons WHERE name='DEN' """

    # ============== center minus tracon (others minus D01 is ok, right?)

    else:
        if path == "within":

            inner_artcc_sql = """ SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='%s'),
    (SELECT ST_Transform(ST_Transform(boundary::geometry,26754),4326) FROM tracons WHERE name='DEN')
) as boundary """  % ctr

        else:
            # ============== union of this tier level and all inside
            if path == "upto":  # it had better be this!

               if ctr == 'ZDV':

                   inner_artcc_sql = """ SELECT boundary::geometry as boundary
                               FROM centers WHERE name='%s' """  % ctr

               else:
                   if ctr in tier_1:
                       inner_artcc_sql = """ SELECT ST_ExteriorRing(
               ST_Union(c.boundary::geometry)) as boundary
               FROM centers c
               WHERE name IN ('ZDV', 'ZLA', 'ZLC', 'ZMP', 'ZKC', 'ZAB')"""

                   else:
                       inner_artcc_sql = """ SELECT ST_ExteriorRing(
               ST_Union(c.boundary::geometry)) as boundary
               FROM centers c
               WHERE name IN ('ZDV', 'ZLA', 'ZLC', 'ZMP', 'ZKC', 'ZAB',
                              'ZOA', 'ZSE', 'ZAU', 'ZID', 'ZME', 'ZFW' ) """

    artcc_sql = """
    -- ============ artcc
  SELECT jsonb_build_object(
    'type',         'Feature',
    'id',           1,  -- watch out for this
    'geometry',     ST_AsGeoJSON(boundary)::jsonb
    ) AS feature
  FROM ( %s) inputs_ctr """ % inner_artcc_sql

    # print("inner_artcc_sql:", inner_artcc_sql)
    # print("artcc_sql:", artcc_sql)

    return(artcc_sql)

# ===========================================================================

# want to do json converstion _later_, but to_dict doesn't know how
# to deal with timestamp, so convert to json and back to dict here :-(

def my_df_to_dict(xxx_df):

    xxx_jsn = xxx_df.to_json(date_format='iso', orient="split",
                                 default_handler=str)
    xxx_dct = json.loads(xxx_jsn)

    return(xxx_dct)

# ===========================================================================

def get_details(lgr, gdate, ctr, path, verbose=False):

    #if args.elapsed: bb = elapsed.Elapsed()

    y_m   = gdate.strftime("%Y_%m")
    yhmhd = gdate.strftime("%Y-%m-%d")

    # tomorrow : FIXME -- month wrap-around needs JOIN on next table!!!
    # tomorrow : FIXME -- month wrap-around needs JOIN on next table!!!

    yhmhd_tom = (gdate + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    distances = get_distances_for_path(path)

    if path != 'full':
        use_ctr = ctr
    else:
        # if ctr = ZZZ then path MUST be within (right?)
        use_ctr = 'ZZZ'

    sql = """SELECT  acid, fid, corner, artcc, dep_apt, arr_apt,
dep_time, arr_time,
%s
FROM fvfb_%s
WHERE artcc = '%s'
AND arr_time >= to_timestamp('%s 08:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
AND arr_time <  to_timestamp('%s 08:00:00+00', 'YYYY-MM-DD HH24:MI:SS+ZZ')
""" % (distances, y_m, use_ctr, yhmhd, yhmhd_tom)

    if verbose: print(sql)
    lgr.debug(sql)

    details_df = pd.read_sql(sql, cssi_engine)

    if verbose: print(details_df)
    lgr.debug(details_df)

    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # make smaller if testing
    details_df = details_df[2:4] if verbose else details_df

    details_dct = my_df_to_dict( details_df )

    #if args.elapsed: bb.end("retr details:" + ctr)

    return(details_df, details_dct)

# ===========================================================================

def get_chart_from_details_OLD_partially_edited(lgr, details_df, ctr, path, source):

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

    dist_col = "HELP_dist"
    if source == "sched"  :  dist_col = "sch_dist"
    if source == "filed"  :  dist_col = "fld_dist"
    if source == "depart" :  dist_col = "dep_dist"
    if source == "at_ent" :  dist_col = "ent_dist"
    if source == "flown"  :  dist_col = "flw_dist"

    cnr_sum_df = details_df.groupby(["arr_qh", "corner"]) [[dist_col]].sum()

    cnr_and_qh = cnr_sum_df.reset_index() \
                    .pivot(index='arr_qh', columns='corner', values=dist_col)

#                         flw_dist
# corner                        ne           nw           se           sw
# arr_qh
# 2020-01-10 05:00:00   228.924232   173.239156   474.044326   332.111915
# 2020-01-10 05:15:00   456.887751          NaN   357.576098   331.772044
# 2020-01-10 05:30:00   391.423476   146.364984   136.074262  1039.217549
# 2020-01-10 05:45:00          NaN   340.448476   348.360392   599.284942

    #cnr_and_qh.rename({
    #             'ne' : "ne_flw",
    #             'se' : "se_flw",
    #             'sw' : "sw_flw",
    #             'nw' : "nw_flw"}, inplace=True, axis=1)

    cnr_and_qh.fillna(0, inplace=True)
    cnr_and_qh.reset_index(inplace=True)

    code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    return ( cnr_and_qh )

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def OLD_CODE():
    sch_cnr_sum_df = None
    ate_cnr_sum_df = None
    flw_cnr_sum_df = None
    details_df = None

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

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    #if args.elapsed: cc.end("form chart:" + ctr)

    return(ate_cnr_dct, flw_cnr_dct, chart_dct)

#############################################################################

def help_get_corner(c_df, corner, gdate):

    xx_data_slice = c_df[c_df['corner']==corner]
    xx_data  = xx_data_slice.drop(['corner'], axis=1)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # fill in missing/0 data
    fill_strt = datetime.datetime(gdate.year, gdate.month, gdate.day, 8, 0, 0)
    fill_step = datetime.timedelta(minutes=15)
    qh_list   = list(xx_data['arr_qh'])

    #print("qh_list=", qh_list)

    for s in range(24*4):

        check = (fill_strt+s*fill_step).strftime("%Y_%m_%d_%H:%M")
        #print("check=", check)

        if check not in qh_list:
            #print("insert:", check)
            #WRONG: xx_data.loc[len(xx_data.index)] = [check, 0]
            #WRONG: xx_data.append([check, 0])
            #xx_data.loc[len(xx_data)] = [check, 0]
            xx_data = xx_data.append({'arr_qh':check, 'flw_dist':0}, ignore_index=True)
            #print("len=", len(xx_data))

    xx_data.sort_values(by="arr_qh", inplace=True)

    #print("xx_data")
    #print(xx_data)

    #xx_data.reset_index(inplace=True)    # any real point in this??
    yy_data = xx_data.reset_index(drop=True)    # any real point in this??

    #print("yy_data")
    #print(yy_data)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    yy_jsn = yy_data.to_json(orient='split', index=False)
    yy_dct = json.loads(yy_jsn)
    return(yy_dct)

# ===================================================================

def get_cnr_bar_from_details(lgr, details_df, gdate, ctr, path, source):

    # get the quarter-hour landing time
    details_df['arr_qh'] = details_df['arr_time'].apply(lambda dt:
         datetime.datetime(dt.year, dt.month, dt.day,
                                              dt.hour,15*(dt.minute // 15)) \
         .strftime("%Y_%m_%d_%H:%M"))

    # ---- get corner data for charts
    # CONSIDER: keep just the 'good' dist column and drop the rest?
    # no, js doesn't use names anyway (for orient='split')

    dist_col = "HELP_dist"
    if source == "sched"  :  dist_col = "sch_dist"
    if source == "filed"  :  dist_col = "fld_dist"
    if source == "depart" :  dist_col = "dep_dist"
    if source == "at_ent" :  dist_col = "ent_dist"
    if source == "flown"  :  dist_col = "flw_dist"

    cnr_qh_df = details_df.groupby(["corner", "arr_qh"]) [[dist_col]].sum()

    cnr_qh_df.reset_index(inplace=True)

    #print(cnr_qh_df)
    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # PROB. could be much better!!!
    ne_dct = help_get_corner(cnr_qh_df, 'ne', gdate)
    se_dct = help_get_corner(cnr_qh_df, 'se', gdate)
    sw_dct = help_get_corner(cnr_qh_df, 'sw', gdate)
    nw_dct = help_get_corner(cnr_qh_df, 'nw', gdate)

    #print(nw_dct)
    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    circ_dct = { 'ne' : ne_dct,
                 'se' : se_dct,
                 'sw' : sw_dct,
                 'nw' : nw_dct }


    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    return(circ_dct)

#############################################################################

# main function called from app.py (if running under Flask)
#               or called from below (if running from command line)
# output is a dictionary to be json-encoded

def get_postg_data_from_asdidb_f20(lgr, gdate, ctr, path, source ):

    lgr.info("get_postg starting")

    main_output = { 'map_data'     : {},
                    'chart_data'   : {},
                    'details_data' : {} }

    lgr.info("ma")
    # OLD: for ctr in den_artccs:

    lgr.info("mb")
    lgr.info(ctr)

    # -------------- part 1: get map geojson

    map_dct = retrieve_path_center_geojson_f20(lgr, gdate, ctr,
                                               path, source, args_verbose)

    lgr.info("have map_dct")

    main_output['map_data'] = map_dct

    # -------------- part 2: get details

    details_df, details_dct = get_details(lgr, gdate, ctr, path, args_verbose)

    main_output['details_data'] = details_dct

    # -------------- part 3: chart details (the MAIN part)

    cnr_qh_dct = get_cnr_bar_from_details(lgr, details_df, gdate, ctr, path, source)

    main_output['chart_data'] = cnr_qh_dct

    # -------------- part 99: the end.

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

    parser.add_argument('-c', '--center', type=str,
            help="artcc to use", default="ZDV")

    parser.add_argument('-p', '--path', type=str,
            help="path type", choices=["within", "upto", "full"], default="within")

    parser.add_argument('-s', '--source', type=str,
            help="source type", default="flown",
            choices=["sched", "filed", "depart", "at_ent", "flown"] )

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

    main_output = get_postg_data_from_asdidb_f20(lgr, args.date, args.center,
                                                 args.path, args.source)

    # nice format
    if args.output == 'p':
        if args.filename is not None:
            with open(args.filename, "w") as fd:
                fd.write(pprint(main_output))
        else:
            pprint(main_output)

    # actual json-encoded data sent to browser
    if args.output == 'j':
        if args.filename is not None:
            with open(args.filename, "w") as fd:
                fd.write(json.dumps(main_output) )
        else:
            pprint(json.dumps(main_output))

    print("written:", args.filename)
