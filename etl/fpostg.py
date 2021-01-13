
# ####################################################################### #
#                               postgis                                   #
# ####################################################################### #

import io
import psycopg2
import geopandas as gpd

# ours
import adaptation
import elapsed

from sqlalchemy import create_engine

# =====================================================================

# note: d.b. access credentials are in dot files
pg_conn = psycopg2.connect(database='meekma')
pg_csr = pg_conn.cursor( )   # calc_scores needs this

# Creating SQLAlchemy's engine to use; FIXME: use env vars!!!
engine = create_engine('postgresql://wturner:@localhost:5432/meekma')

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

def get_corners(apt):

    corners = str(tuple(adaptation.corners[apt].values()))

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
    return ("ST_GeomFromText('" + s + "',4326)")

# --------------------------------------------------------------------

# DROP and CREATE the table

def drop_cre8_sched(sch_tbl):

    drp = "DROP TABLE IF EXISTS %s ;" % sch_tbl
    pg_csr.execute(drp)

    # TODO: rename geometry column to sched_path
    # TODO: recast Geometry column to Geography (but dont think it matters;
    #        Postg says geometry with 4326 is equivalent to geography)

    cre8 = """CREATE table %s (
    acid         text,
    fid          bigint,
    flight_index integer,
    orig_time    timestamptz,
    dep_time     timestamptz,
    arr_time     timestamptz,
    dept_aprt    text,
    arr_aprt     text,
    source_type  text,
    waypoints    text,
    geometry     Geometry(LineString, 4326)
); """ % sch_tbl

    pg_csr.execute(cre8)
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
        'DEPT_APRT'    : 'dept_aprt',
        'ARR_APRT'     : 'arr_aprt',
        'WAYPOINTS'    : 'waypoints'
        }, inplace=True)

    # make a text / wkt column of the (shapely) linestring

    sch_df['geometry'] = sch_df['sched_path'].apply(lambda g: g.wkt)

    # and get rid of the shapely column
    sch_df.drop('sched_path', inplace=True, axis=1)

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
         " (acid,fid,flight_index,orig_time, dep_time, arr_time,dept_aprt," + \
        "arr_aprt, source_type, waypoints, geometry)" + \
        "values(" + \
            sq(row['acid']) + ',' + \
           str(row['fid']) + ',' + \
           str(row['flight_index']) + ',' + \
        sq(str(row['orig_time'])) + ',' + \
        sq(str(row['dep_time'])) + ',' + \
        sq(str(row['arr_time'])) + ',' + \
            sq(row['dept_aprt']) + ',' + \
            sq(row['arr_aprt']) + ',' + \
            sq(row['source_type']) + ',' + \
            sq(row['waypoints']) + ',' + \
            pg(row['geometry']) + ');'

        # and actually do the insert

        pg_csr.execute(sql)

        good += 1

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
    # FIXME!!!!!!!!!!!!!!!!!!!!!

    cre8 = """CREATE table %s (
    flt_ndx  integer,
    acid     text,
    traj     TGeogPoint
); """ % flw_tbl

    if verbose: print(cre8)
    pg_csr.execute(cre8)
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

