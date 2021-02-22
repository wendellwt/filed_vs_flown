
# ####################################################################### #
#                               postgis                                   #
# ####################################################################### #

# note: this file contains _all_ postgis subroutines used by both
#  filedflown.py and (the now ole and superceeded) oracle2postg.py

import io
import sys
import psycopg2
import geopandas as gpd

import elapsed

# =====================================================================
import os
from sqlalchemy import create_engine

username = os.environ.get('PGUSER')
password = os.environ.get('PGPASSWORD')
database = os.environ.get('PGDATABASE')
host     = os.environ.get('PGHOST')

# d.b. access credentials are in env vars
pg_conn = psycopg2.connect(database=database)
pg_csr = pg_conn.cursor( )

# the sqlalchemy way:
engine = create_engine('postgresql://' + \
                 username + ':' + password + '@' + host + ':5432/' + database)

engine.execute("SET TIME ZONE 'UTC';")  # date has timezone ???

# =====================================================================

# get the (single) geojson descr of artcc center without tracon

def get_gjson_of_ctr(ctr, apt=None, args_verbose=False):
    """ return geojson of center bounary, and optionally subtract tracon."""

    if apt is not None:

# what we are doing:
#   * retrieve position of DEN
#   * ST_Transform that to an EPSG code that will 'look nice' around Colorado
#   * construct an ST_Buffer (which is 42*6076 feet) from/around that positon
#   * 'put it back' to EPSG:4326
#   * subtract that from ZDV (using ST_Difference)
#   * ST_Transform that into 4326 (is this reduntant now?)
#   * have PostGIS convert it to GeoJSON

# found EPSG:26754    which is Colorado SPECIFIC!  but it looks GOOD!!
# but UoM: ftUS
# https://epsg.org/crs_26754/NAD27-Colorado-Central.html?sessionkey=ymbyhaj6ze

        sql = """SELECT ST_AsGeoJSON(ST_Transform(
    (select ST_Difference(
(select boundary from centers where name = '%s')::geometry,
(select ST_Transform(ST_Buffer(
         ST_Transform(position::geometry,26754),42*6076),4326) AS tracon
         FROM airports WHERE ident ='%s')::geometry
)) ,4326));""" % (ctr, apt)

    else:
        sql = """SELECT ST_AsGeoJSON(ST_Transform(
                (select boundary from centers where name = '%s')::geometry,
                4326));""" % (ctr)

    if args_verbose: print(sql)

    pg_csr.execute(sql)
    ret = pg_csr.fetchall()

    return(ret)

# ==========================================================================

# note: caller prob. needs to do a wkb.loads() on the result

def get_shape_of_ctr(ctr, args_verbose=False):
    """ return shape of center bounary."""

    sql = "select boundary from centers where name = '%s'" % ctr

    if args_verbose: print(sql)

    pg_csr.execute(sql)
    ret = pg_csr.fetchall()

    return(ret)

# ==========================================================================

# >>> used adaptation.py, which is now a toml file

#def get_corners(apt):
#
#    corners = str(tuple(adaptation.corners[apt].values()))
#
#    sql = """select ident, position
#FROM points
#WHERE ident IN """ + corners + ";"
#
#    corner_gf = gpd.GeoDataFrame.from_postgis(sql, pg_conn,
#                                              geom_col='position' )
#    return(corner_gf)

# ==========================================================================

def get_corner_pos(ident):

    sql = "select ST_AsText(position) FROM points WHERE ident = '" + ident + "';"

    pg_csr.execute(sql)
    ret = pg_csr.fetchone()

    return(ret[0])

# ==========================================================================

def get_corners_by_list(corner_list):

    corners = str(tuple(corner_list))

    sql = """select ident, position
FROM points
WHERE ident IN """ + corners + ";"

    corner_gf = gpd.GeoDataFrame.from_postgis(sql, pg_conn,
                                              geom_col='position' )
    return(corner_gf)

# ==========================================================================

def sq(s):
    return ("'" + s + "'")

def pg(s):
    return ("ST_GeogFromText('" + s + "')")

# --------------------------------------------------------------------

# DROP and CREATE the table

def drop_cre8_sched(sch_tbl):

    drp = "DROP TABLE IF EXISTS %s ;" % sch_tbl
    pg_csr.execute(drp)

    # done: rename geometry column to sched_path
    # TODO: recast Geometry column to Geography (but dont think it matters;
    #        Postg says geometry with 4326 is equivalent to geography)
    #        but NO, later it says that ST_Length is cartesian for geom,
    #        spheroid for geography

    cre8 = """CREATE table %s (
    acid         text,
    fid          bigint,
    flight_index integer,
    orig_time    timestamptz,
    dep_time     timestamptz,
    arr_time     timestamptz,
    dep_apt      text,
    arr_apt      text,
    source_type  text,
    ac_type      text,
    waypoints    text,
    geography    Geography(LineString, 4326)
); """ % sch_tbl

    pg_csr.execute(cre8)

    # FIXME: please set your own permissions !!!!!
    fixme="grant select on all tables in schema public to meow_user;"
    pg_csr.execute(fixme)

    pg_conn.commit()           # commit both of them

# --------------------------------------------------------------------

# note: pandas as input, not geopandas :-(

def write_sched_df_as_loop(sch_df, sch_tbl, verbose=False):

    pe = elapsed.Elapsed()
    print("writing sched table")

    drop_cre8_sched(sch_tbl)

    # ----------------------------------------

    # rename to all lowercase so pg will be ok with it

    sch_df.rename(columns={
        'ACID'         : 'acid',
        'FID'          : 'fid',
        'FLIGHT_INDEX' : 'flight_index',
        'ORIG_TIME'    : 'orig_time',
        'SOURCE_TYPE'  : 'source_type',
        'DEP_TIME'     : 'dep_time',
        'ARR_TIME'     : 'arr_time',
        'DEPT_APRT'    : 'dep_apt',   # renamed
        'ARR_APRT'     : 'arr_apt',   # renamed
        'ACFT_TYPE'    : 'ac_type',   # renamed
        'WAYPOINTS'    : 'waypoints'
        }, inplace=True)

    # make a text / wkt column of the (shapely) linestring

    if verbose: print("lambda of wkt")

    #geom: sch_df['geography'] = sch_df['sched_path'].apply(lambda g: g.wkt)
    # make our own ewkt: (NO, all is 4326 anyway)
    sch_df['geography'] = sch_df['sched_path'].apply(lambda g: g.wkt)

    # ewkt = ";".join(["SRID=4326", wkt])


    # and get rid of the shapely column
    sch_df.drop('sched_path', inplace=True, axis=1)

    # and rename the wkt column to the postgis column
    #TODO: RENAME COLUMN LATER: sch_df.rename(columns={ 'sched_path_wkt' : 'sched_path'})

    if verbose: print("sch_df")
    if verbose: print(sch_df)

    bad = 0
    good = 0

    # in a VERY AWKWARD loop, insert the scheduled linestrings one-by-one
    # because after A WHOLE DAY I couldn't get GeoPandas to output anything

    for index, row in sch_df.iterrows():

        # maybe the dropna did this beforehand

        if (str(row['orig_time']) == 'NaT') |  \
           (str(row['dep_time' ]) == 'NaT') | \
           (str(row['arr_time' ]) == 'NaT'):
            print("bad time:", str(row['orig_time']), str(row['dep_time' ]), str(row['arr_time' ]))
            bad += 1
            continue

        # and genrate the insert statement -- FIXME: include dynamic tablename

        sql = "INSERT INTO " + sch_tbl + \
         " (acid,fid,flight_index,orig_time, dep_time, arr_time,dep_apt," + \
        "arr_apt, source_type, ac_type, waypoints, geography)" + \
        "values(" + \
            sq(row['acid']) + ',' + \
           str(row['fid']) + ',' + \
           str(row['flight_index']) + ',' + \
        sq(str(row['orig_time'])) + ',' + \
        sq(str(row['dep_time'])) + ',' + \
        sq(str(row['arr_time'])) + ',' + \
            sq(row['dep_apt']) + ',' + \
            sq(row['arr_apt']) + ',' + \
            sq(row['source_type']) + ',' + \
            sq(row['ac_type']) + ',' + \
            sq(row['waypoints']) + ',' + \
            pg(row['geography']) + ');'

        # and actually do the insert

        pg_csr.execute(sql)

        good += 1

    # TODO rename 'geometry' column to be 'sched_path'

    pg_conn.commit()     # only now do the commit

    print("sched paths written; good: %d  bad: %d" % (good, bad))

    pe.end("postg write")

# psycopg2.errors.InvalidDatetimeFormat: invalid input syntax for type timestamp with time zone: "NaT"
# LINE 1: ...Z6092',20200110485019,44851,'2020-01-09 09:37:08','NaT','202...

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# write these FIDs to temp postgresql table

def write_tz_to_temp_postgis_table(no_dups, temp_tablename):

    et = elapsed.Elapsed()

    drp = "DROP TABLE IF EXISTS %s ;" % temp_tablename
    pg_csr.execute(drp)
    pg_conn.commit()           # Q: need commit here???

    # https://stackoverflow.com/questions/23103962/how-to-write-dataframe-to-postgres-table
    # not sure what this does, or how it works, but it is LIGHTNING FAST
    # (p.s.: there is (possibly) an even faster version listed there)

    print("write to_sql, len=" + str(len(no_dups)))

    no_dups.head(0).to_sql(name      = temp_tablename,
                           con       = engine,
                           if_exists = 'replace',
                           index     = False) #truncates the table

    conn = engine.raw_connection()
    cur = pg_conn.cursor()
    output = io.StringIO()
    no_dups.to_csv(output, sep='\t', header=False, index=False)

    print("csv written")

    output.seek(0)

    # actually do the sql copy here
    cur.copy_from(output, temp_tablename, null="") # null values become ''

    print("cur.copy_from")

    conn.commit()

    print("commit")
    et.end("write to temp table")

    return(temp_tablename, len(no_dups))  # for stats at end
                            # MISLEADING: this is the number of POINTS

# %%%%%%%%%%%%%%%%%%%%%%%%%%%% BREAK %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# sqlqlchemy used to do ths for us

def drop_create_flown(flw_tbl, verbose=False):

    # ---------------- DROP and CREATE the table

    drp = "DROP TABLE IF EXISTS %s ;" % flw_tbl
    if verbose: print(drp)
    pg_csr.execute(drp)

    # FIXME!!!!!!!!!!!!!!!!!!!!!
    # FIXME put more metadata in here !!!!!!!
    # FIXME add departure, arrival airport locations (but what about times???)
    # FIXME add CORNER POST
    # FIXME!!!!!!!!!!!!!!!!!!!!!

    cre8 = """CREATE table %s (
    flight_index integer,
    acid         text,
    flown_path   TGeogPoint
); """ % flw_tbl

    if verbose: print(cre8)
    pg_csr.execute(cre8)

    # FIXME: please set your own permissions !!!!!
    fixme="grant select on all tables in schema public to meow_user;"
    pg_csr.execute(fixme)

    pg_conn.commit()           # commit both of them

# ----------------------------------------

def temp_points_table_to_mdb_table(temp_tablename, flown_tablename, verbose=False):

    ef = elapsed.Elapsed()

    # use INSERT/tgeogpointseq to read temp tbl, convert to MDB elements,
    # and write to the tz table

    # maybe postgis insert is fixed and don't need to quote or ucase cols now

    print("tgeogpoint")

    # jan12: removed ACT_DATE

    ins = 'INSERT INTO ' + flown_tablename + \
            ' SELECT "FLIGHT_INDEX", "ACID", ' + \
            ' tgeogpointseq(array_agg(tgeogpointinst( ' + \
            ' ST_SetSRID(ST_MakePoint("LON","LAT"), 4326), "POSIT_TIME") ' + \
                ' ORDER BY "POSIT_TIME"))' + \
             ' FROM ' + temp_tablename + \
             ' GROUP BY "FLIGHT_INDEX", "ACID" ' + \
             " ON CONFLICT DO NOTHING ; "

    # this fixed (caused error not to occur and processing completed):
    #   " ON CONFLICT DO NOTHING ; "
    if verbose : print(ins)

    try:
        engine.execute(ins)
    except:
        print("engine.execute(ins) FAILED")
        print("sql was:" + ins)

    pg_conn.commit()           # Q: will this work on the engine items???
    print("inserted.")

    ef.end("insert from temp to flown")


# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#CREATE TABLE fvf_2020_03 (
#    acid          text,
#    fid           bigint,
#    corner        text,
#    artcc         text,
#    dep_apt       text,
#    arr_apt       text,
#    flw_dist      float,
#    b4_ent_dist   float,
#    b4_dep_dist   float,
#    dep_time      timestamptz,
#    arr_time      timestamptz,
#    flw_geog      Geography,
#    b4_ent_geog   Geography,
#    b4_dep_geog   Geography
#);

# ==================================================================

from geoalchemy2 import Geography, WKTElement

# write pandas df WITH MULTIPLE GEOGRAPHY COLUMNS out to postgis

import code                     # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
import time

def write_ff_to_postgis(fvf_tbl, ctr_df, ctr_name_HELP):
    global engine, pg_conn, pg_csr # HELP!!!

    ctr_df.rename( {
        'flw_path'    : 'flw_geog',
        'b4_ent_path' : 'b4_ent_geog',
        'b4_dep_path' : 'b4_dep_geog',
        }, axis=1, inplace=True)

    ctr_gf = gpd.GeoDataFrame(ctr_df, geometry='flw_geog')

    # ?????????????????????????????????????????
    # TEST FOR Geography elements that may cause PostGIS to CRASH

    # this WASN'T it, but I suppose it doesn't hurt...
    # (I think it does help sometimes)
    ctr_gf = ctr_gf.loc[ctr_gf['flw_geog'   ].apply(lambda p: p.is_empty == False )]
    ctr_gf = ctr_gf.loc[ctr_gf['b4_ent_geog'].apply(lambda p: p.is_empty == False )]
    ctr_gf = ctr_gf.loc[ctr_gf['b4_dep_geog'].apply(lambda p: p.is_empty == False )]

    # as a TEST, keep just the FLOWN tracks that are really LINESTRINGS
    ctr_gf = ctr_gf.loc[ctr_gf['flw_geog'   ].apply(lambda p: p.geom_type == 'LineString' )]
    ctr_gf = ctr_gf.loc[ctr_gf['b4_ent_geog'].apply(lambda p: p.geom_type == 'LineString' )]
    ctr_gf = ctr_gf.loc[ctr_gf['b4_dep_geog'].apply(lambda p: p.geom_type == 'LineString' )]

    set_of_types = set()

    ctr_gf['flw_geog'   ].apply(lambda g: set_of_types.add(g.geom_type))
    ctr_gf['b4_ent_geog'].apply(lambda g: set_of_types.add(g.geom_type))
    ctr_gf['b4_dep_geog'].apply(lambda g: set_of_types.add(g.geom_type))

    print("set_of_types")
    print(set_of_types)

    set_of_simple = set()
    ctr_gf['flw_geog'   ].apply(lambda g: set_of_simple.add(g.is_simple))
    ctr_gf['b4_ent_geog'].apply(lambda g: set_of_simple.add(g.is_simple))
    ctr_gf['b4_dep_geog'].apply(lambda g: set_of_simple.add(g.is_simple))
    print("set_of_simple")
    print(set_of_simple)

    set_of_valid = set()
    ctr_gf['flw_geog'   ].apply(lambda g: set_of_valid.add(g.is_valid))
    ctr_gf['b4_ent_geog'].apply(lambda g: set_of_valid.add(g.is_valid))
    ctr_gf['b4_dep_geog'].apply(lambda g: set_of_valid.add(g.is_valid))
    print("set_of_valid")
    print(set_of_valid)

    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ?????????????????????????????????????????

    # ---- 1) convert each geom from shapely to wkt

    # .buffer(0) on ch is prob. redundant
    # but it does make polygon a valid one

    ctr_gf.set_geometry('flw_geog', inplace=True)  # so .buffer() will work

    ctr_gf['flw_geog_wkt'] = ctr_gf['flw_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    ctr_gf.set_geometry('b4_ent_geog', inplace=True)

    ctr_gf['b4_ent_geog_wkt'] = ctr_gf['b4_ent_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    ctr_gf.set_geometry('b4_dep_geog', inplace=True)

    ctr_gf['b4_dep_geog_wkt'] = ctr_gf['b4_dep_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    # ---- 2) drop the shapely columns

    ctr_gf.drop(['flw_geog', 'b4_ent_geog', 'b4_dep_geog'],  axis=1,
                                                           inplace=True)

    # ---- 3) rename wkt columns to match PostGIS

    ctr_gf.rename( {
        'flw_geog_wkt'    : 'flw_geog',
        'b4_ent_geog_wkt' : 'b4_ent_geog',
        'b4_dep_geog_wkt' : 'b4_dep_geog',
        }, axis=1, inplace=True)

    # ---- 4) finish off to ensure it is a proper geodataframe
    ctr_gf.crs = {'init' :'epsg:4326'}

    ctr_gf.to_csv(fvf_tbl + '_' + ctr_name_HELP + ".csv")  # <<<<<<< HELP <

    # note: flw_geom column is now _not_ a (shapely) geometry column,
    #  but a wkt that looks like one
    #wrong: ctr_gf.set_geometry('flw_geog', inplace=True)  # pointless???

    foo = ctr_gf.reset_index(drop=True)  # HELP: may be some sort of index issue
    try:
        foo.to_sql(fvf_tbl, engine, if_exists='append', index=False,
             dtype={'flw_geog'   : Geography(),   # use col id for type & srid(?)
                    'b4_ent_geog': Geography(),
                    'b4_dep_geog': Geography()
                    })
    except:
        print(">>>>>>>>>>>>> HELP!!!")
        print(ctr_gf)
        print(">>>>>>>>>>>>> HELP!!!")

        print("sleeping...")
        time.sleep(20)
        print("awaken")
        #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # TODO: RECONNECT!!!!!!!!!!!!!
        # d.b. access credentials are in env vars
        pg_conn = psycopg2.connect(database=database)
        pg_csr = pg_conn.cursor( )

        # the sqlalchemy way:
        engine = create_engine('postgresql://' + \
            username + ':' + password + '@' + host + ':5432/' + database)

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def write_ff_to_postgis_loop(fvf_tbl, ctr_df, ctr_name_HELP):

    ctr_df.rename( {
        'flw_path'    : 'flw_geog',
        'b4_ent_path' : 'b4_ent_geog',
        'b4_dep_path' : 'b4_dep_geog',
        }, axis=1, inplace=True)

    # ---- 1) convert each geom from shapely to wkt

    # .buffer(0) on ch is prob. redundant
    # but it does make polygon a valid one

    ctr_df['flw_geog_wkt'] = ctr_df['flw_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    ctr_df['b4_ent_geog_wkt'] = ctr_df['b4_ent_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    ctr_df['b4_dep_geog_wkt'] = ctr_df['b4_dep_geog'] \
                        .apply(lambda x: WKTElement(x.wkt, srid=4326))

    # ---- 2) drop the shapely columns

    #ctr_df.drop(['flw_geog', 'b4_ent_geog', 'b4_dep_geog'],  axis=1,
    #                                                       inplace=True)

    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    for index, row in ctr_df.iterrows():

        print(row)

        sql = """
INSERT INTO fvf_2020_12 (fid, acid, dep_time, arr_time,
  dep_apt, arr_apt,
  b4_ent_dist, b4_dep_dist, flw_dist,
  corner, artcc,
  b4_dep_geog,
  b4_ent_geog,
  flw_geog)
VALUES (""" + \
     str(row['fid']) + ',' + \
     sq(row['acid']) + ',' + \
     sq(row['dep_time'].isoformat()) + '::timestamp,' + \
     sq(row['arr_time'].isoformat()) + '::timestamp,' + \
     sq(row['dep_apt']) + ',' + \
     sq(row['arr_apt']) + ',' + \
     str(row['b4_ent_dist']) + ',' + str(row['b4_dep_dist']) + ',' + str(row['flw_dist']) + ',' + \
     sq(row['corner']) + ',' + sq(row['artcc']) + ',' + \
     "ST_GeogFromText('SRID=4326;" + row['b4_dep_geog'].wkt + "')," + \
     "ST_GeogFromText('SRID=4326;" + row['b4_ent_geog'].wkt + "')," + \
     "ST_GeogFromText('SRID=4326;" + row['flw_geog'   ].wkt + "'))"

        print(sql)

        #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        pg_csr.execute(sql)
        pg_conn.commit()

# ==================================================================

cssi_username = os.environ.get('CSSI_USER')
cssi_password = os.environ.get('CSSI_PASSWORD')
cssi_database = os.environ.get('CSSI_DATABASE')
cssi_host     = os.environ.get('CSSI_HOST')

# the CSSI sqlalchemy way:
cssi_engine = create_engine('postgresql://' + \
            cssi_username + ':' + cssi_password + '@' + cssi_host + \
                            ':5432/' + cssi_database)

# ==================================================================

# feb20 - add all paths

cre8_fvf = """ CREATE TABLE IF NOT EXISTS %s (
    acid          text,
    fid           bigint,
    corner        text,
    artcc         text,
    ac_type       text,

    dep_apt       text,
    arr_apt       text,
    dep_time      timestamptz,
    arr_time      timestamptz,

    opsday        date,

    -- all 5 paths & distances (actually within for real, full if zzz)
    scheduled_within_dist  float,
    scheduled_within_geog  Geography,

    first_filed_within_dist  float,
    first_filed_within_geog  Geography,

    last_filed_within_dist  float,
    last_filed_within_geog  Geography,

    flown_within_dist  float,
    flown_within_geog  Geography,

    -- this is used for real artcc, but not used for zzz
    at_entry_within_dist  float,
    at_entry_within_geog  Geography,

    -- all 5 paths & distances
    scheduled_upto_dist  float,
    scheduled_upto_geog  Geography,

    first_filed_upto_dist  float,
    first_filed_upto_geog  Geography,

    last_filed_upto_dist  float,
    last_filed_upto_geog  Geography,

    flown_upto_dist  float,
    flown_upto_geog  Geography

    -- not used for full or upto
    --at_entry_upto_dist  float,
    --at_entry_upto_geog  Geography,

);"""

# ==================================================================
#from geoalchemy2 import Geography, WKTElement

# write pandas df WITH MULTIPLE GEOGRAPHY COLUMNS out to postgis

def write_ff_to_postgis_cssi(y_m, ctr_df):

    fvf_tbl = "fvfb_" + y_m   # feb20: 'b' added

    cssi = elapsed.Elapsed()

    cre8_sql = cre8_fvf % fvf_tbl
    #print(cre8_sql)

    cssi_engine.execute(cre8_sql)

    ctr_df.rename( { 'OPSDAY' : 'opsday'},  axis=1, inplace=True)

    ctr_gf = gpd.GeoDataFrame(ctr_df, geometry='flown_path')

    # ---- 1) convert each geom from shapely to wkt

    ctr_gf['scheduled_within_geog_wkt'  ] = ctr_gf['scheduled_within_path'  ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['first_filed_within_geog_wkt'] = ctr_gf['first_filed_within_path'].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['last_filed_within_geog_wkt' ] = ctr_gf['last_filed_within_path' ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['flown_within_geog_wkt'      ] = ctr_gf['flown_within_path'      ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['at_entry_within_geog_wkt'   ] = ctr_gf['at_entry_within_path'   ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['scheduled_upto_geog_wkt'    ] = ctr_gf['scheduled_upto_path'    ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['first_filed_upto_geog_wkt'  ] = ctr_gf['first_filed_upto_path'  ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['last_filed_upto_geog_wkt'   ] = ctr_gf['last_filed_upto_path'   ].apply(lambda x: WKTElement(x.wkt, srid=4326))
    ctr_gf['flown_upto_geog_wkt'        ] = ctr_gf['flown_upto_path'        ].apply(lambda x: WKTElement(x.wkt, srid=4326))

    # ---- 2) drop the shapely columns

    ctr_gf.drop([ 'scheduled_within_path',
                  'first_filed_within_path',
                  'last_filed_within_path',
                  'flown_within_path',
                  'at_entry_within_path',
                  'scheduled_upto_path',
                  'first_filed_upto_path',
                  'last_filed_upto_path',
                  'flown_upto_path',
                  'flown_path',      # <<<< HELP:  why was this left in??
                  'FLIGHT_INDEX',    # <<<< HELP:  why was this left in??
                 ],  axis=1, inplace=True)

    # ---- 3) rename wkt columns back to 'good' names to match PostGIS

    ctr_gf.rename( {
        'scheduled_within_geog_wkt'   : 'scheduled_within_geog',
        'first_filed_within_geog_wkt' : 'first_filed_within_geog',
        'last_filed_within_geog_wkt'  : 'last_filed_within_geog',
        'flown_within_geog_wkt'       : 'flown_within_geog',
        'at_entry_within_geog_wkt'    : 'at_entry_within_geog',
        'scheduled_upto_geog_wkt'     : 'scheduled_upto_geog',
        'first_filed_upto_geog_wkt'   : 'first_filed_upto_geog',
        'last_filed_upto_geog_wkt'    : 'last_filed_upto_geog',
        'flown_upto_geog_wkt'         : 'flown_upto_geog',
                                            }, axis=1, inplace=True)

    # ---- 4) finish off to ensure it is a proper geodataframe
    #WARNING: ctr_gf.set_geometry('flown_within_geog', inplace=True)  # so .crs() will work
    # HELP: is this needed???: ctr_gf.crs = {'init' :'epsg:4326'}

    # ---- 5) setup for .to_sql() via sqlalchemy
    pg_dtype = {
        'scheduled_within_geog'   : Geography(),
        'first_filed_within_geog' : Geography(),
        'last_filed_within_geog'  : Geography(),
        'flown_within_geog'       : Geography(),
        'at_entry_within_geog'    : Geography(),

        'scheduled_upto_geog'     : Geography(),
        'first_filed_upto_geog'   : Geography(),
        'last_filed_upto_geog'    : Geography(),
        'flown_upto_geog'         : Geography() }

    #print(" about to write to asdi-db")
    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    try:
        ctr_gf.to_sql(fvf_tbl, cssi_engine, if_exists='append', index=False,
                                  dtype = pg_dtype)


    except Exception as exc:
        #print traceback.format_exc()
        print(exc)
        print(">>>>>>>>>>>>> HELP!!!")
        print(ctr_gf)
        print(">>>>>>>>>>>>> HELP!!!")
        sys.exit(1)

    cssi.end("wrote cssi postgis")

    #print("write to asdi-db finished.")
    # code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

