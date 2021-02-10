#!/home/data/local/bin/python3.7


# ######################  oracle  #########################

import os
import pandas as pd
import datetime
import cx_Oracle as cxo
import elapsed

host     = os.environ.get('EXTR1_IP')
port     = os.environ.get('EXTR1_PORT')
service  = os.environ.get('EXTR1_SERVICE')
username = os.environ.get('EXTR1_USER')
password = os.environ.get('EXTR1_PASS')

# ######################  oracle + plain to extr1  #######################

ex_dsn_tns = cxo.makedsn(host, port, service_name=service)
ex_conn    = cxo.connect(username, password, ex_dsn_tns)

# ######################  oracle + sqlalchemy to filed_vs_flown  ########

from sqlalchemy import types, create_engine

host     = os.environ.get('FLVL_IP')
port     = os.environ.get('FLVL_PORT')
service  = os.environ.get('FLVL_SERVICE')
username = os.environ.get('FLVL_USER')
password = os.environ.get('FLVL_PASS')

credentials = 'oracle+cx_oracle://' + \
               username + ':' + password + '@' + host + ':' + port + \
              '/?service_name=' + service

# q: should this be named sq_engine???
sq_conn = create_engine(credentials, max_identifier_length=30)

# ======================================================================
# this doesn't seem to hurt...

with sq_conn.connect() as sq_con:

    sql_utc = "ALTER SESSION SET TIME_ZONE='UTC'"

    sq_con.execute(sql_utc)

ex_csr = cxo.Cursor(ex_conn)
ex_csr.execute(sql_utc)

# ########################################################################## #

wwt_5 = ('ATL', 'DCA', 'DEN', 'SEA', 'STL')

opsnet_45  = ("ABQ", "ATL", "BNA", "BOS", "BWI", "CLE", "CLT", "CVG", "DCA",
                "DEN", "DFW", "DTW", "EWR", "FLL", "HOU", "IAD", "IAH", "IND",
                "JFK", "LAS", "LAX", "LGA", "MCI", "MCO", "MDW", "MEM", "MIA",
                "MSP", "MSY", "OAK", "ORD", "PBI", "PDX", "PHL", "PHX", "PIT",
                "RDU", "SAN", "SEA", "SFO", "SJC", "SLC", "STL", "TEB", "TPA")

# consider using this list of airports...
aspm_77  = ("ABQ", "ANC", "ATL", "AUS", "BDL", "BHM", "BNA", "BOS", "BUF",
              "BUR", "BWI", "CLE", "CLT", "CVG", "DAL", "DAY", "DCA", "DEN",
              "DFW", "DTW", "EWR", "FLL", "GYY", "HNL", "HOU", "HPN", "IAD",
              "IAH", "IND", "ISP", "JAX", "JFK", "LAS", "LAX", "LGA", "LGB",
              "MCI", "MCO", "MDW", "MEM", "MHT", "MIA", "MKE", "MSP", "MSY",
              "OAK", "OGG", "OMA", "ONT", "ORD", "OXR", "PBI", "PDX", "PHL",
              "PHX", "PIT", "PSP", "PVD", "RDU", "RFD", "RSW", "SAN", "SAT",
              "SDF", "SEA", "SFO", "SJC", "SJU", "SLC", "SMF", "SNA", "STL",
              "SWF", "TEB", "TPA", "TUS", "VNY")

# ########################################################################## #

# get everything we can from oracle for flights to this airport on the ops day

import sys

def read_ops_day_data(ops_date, arr_apt, args_verbose):

    # ---- ---- get from tables for yesterday, today, and tomorrow

    yestr = (ops_date - datetime.timedelta(days=1)).strftime("%Y%m%d")
    today = (ops_date                             ).strftime("%Y%m%d")
    tomor = (ops_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

    #ora_tbls = "(SELECT * FROM ROUTE_" + yestr + "@ETMSREP UNION ALL " + \
    #            "SELECT * FROM ROUTE_" + today + "@ETMSREP UNION ALL " + \
    #            "SELECT * FROM ROUTE_" + tomor + "@ETMSREP) "

    ora_tbls = "(SELECT * FROM ROUTE_" + yestr + "@ETMSREP WHERE FID > 0 UNION ALL " + \
                "SELECT * FROM ROUTE_" + today + "@ETMSREP WHERE FID > 0 UNION ALL " + \
                "SELECT * FROM ROUTE_" + tomor + "@ETMSREP WHERE FID > 0 ) "

    # NOT: this: tz_diff = +7 # hours to get to utc
    # new def: ops day it 8 (am) UTC to 8(am) UTC

    od_end = ops_date + datetime.timedelta(days=1)
    ops_day_strt = datetime.datetime(ops_date.year, ops_date.month, ops_date.day, 8, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
    ops_day_end  = datetime.datetime(od_end.year,   od_end.month,   od_end.day,   8, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

    arr_time = "arr_time >= to_timestamp_tz('" + ops_day_strt + "+0:00', 'YYYY-MM-DD HH24:MI:SSTZH:TZM') " + \
          " AND arr_time <= to_timestamp_tz('" + ops_day_end  + "+0:00', 'YYYY-MM-DD HH24:MI:SSTZH:TZM')"

    # use one of these:
    #apt_where = " = '" + arr_apt + "'"
    apt_where = " in ('" + "','".join(opsnet_45) + "') "

    sql = """SELECT acid, fid, flight_index, orig_time, source_type,
             dep_time, arr_time, dept_aprt, arr_aprt, acft_type, waypoints
FROM %s
WHERE %s
AND arr_aprt %s """ % (ora_tbls, arr_time, apt_where)

## ORDER BY orig_time""" % (ora_tbls, arr_time, apt_where)

    if args_verbose: print(sql)

    ora_df = pd.read_sql(sql, con=ex_conn)

    # if args_verbose: print(ora_df)

    return(ora_df)

# ########################################################################## #

#   get bunches of fids at one time from oracle

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ########################################################################## #

max_fids_at_once = 990

# get all track points for all flights
# NOTE: if len(fids) > 999 it will BREAK ORACLE

def get_all_tz(ops_date, fids, args_verbose):

    print("beginning to query oracle for all tz for ", len(fids), "fids")
    et = elapsed.Elapsed()

    # ---- ---- get from tables for yesterday, today, and tomorrow

    yestr = (ops_date - datetime.timedelta(days=1)).strftime("%Y%m%d")
    today = (ops_date                             ).strftime("%Y%m%d")
    tomor = (ops_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

    ora_tbls = "(SELECT * FROM TZ_" + yestr + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + today + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + tomor + "@ETMSREP) "

    # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

    ora_df_list = []

    for fid_group in chunks(fids, max_fids_at_once):

        qTracks = "SELECT fid, flight_index, acid, posit_time," + \
                  " round(cur_lat/60.0,5)  as lat, " + \
                  " round(cur_lon/-60.0,5) as lon  " + \
                  " FROM " + ora_tbls + \
                  " WHERE fid IN (" + ','.join(map(str,fid_group)) + ")" + \
                  " AND point_status=-1 "

            # jan 12: " ORDER BY flight_index, posit_time"    # -- just to be sure

        if args_verbose: print(qTracks)

        if (args_verbose):
            this_df = pd.read_sql(qTracks, con=ex_conn)
            print(this_df)
            ora_df_list.append(this_df)
        else:
            print("querying oracle for", len(fid_group), "fids")

            ora_df_list.append(pd.read_sql(qTracks, con=ex_conn))

            #print("received")

    ora_df = pd.concat(ora_df_list)

    # if args_verbose: print(ora_df)
    print("finished query oracle; found", len(ora_df), "tz reports")
    et.end("read tz from oracle")

    return(ora_df)

# ########################################################################## #

# get all track points for all flights

def get_all_tz_using_temp(ops_date, fids, args_verbose):

    print("using temp to query oracle for all tz for ", len(fids), "fids")
    et = elapsed.Elapsed()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ex_csr = cxo.Cursor(ex_conn)

    #print("for")
    #for row in ex_csr.execute("select fid from temp_table_session6 where rownum < 10"):
    #    print(row)
    #sys.exit(1)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#    cre8 = """create global temporary table temp_table_session6
#on commit preserve rows
#as
#select FID from tz_20190613@etmsrep where 1=0
#"""

    #done: print(cre8)

    #done: ex_csr.execute(cre8)
    #done: ex_conn.commit()

    # if no create, is this needed???
    ex_csr.execute("delete from temp_table_session6")
    ex_conn.commit()

    #done: print("temp session table created")

    # https://stackoverflow.com/questions/14904033/how-can-i-do-a-batch-insert-into-an-oracle-database-using-python
    # build rows for each date and add to a list of rows we'll use to insert as a batch
    rows = []
    for k in range(len(fids)):
        row = (fids[k],)
        rows.append(row)

    #aa = elapsed.Elapsed()
    # insert all of the rows as a batch and commit
    ex_csr.prepare('insert into temp_table_session6 (fid) values (:FID)')
    ex_csr.executemany(None, rows)
    ex_conn.commit()

    #aa.end("temp session table inserted")
    #print("temp session table inserted")

    #print("for")
    #for row in ex_csr.execute("select fid from temp_table_session6 where rownum < 100"):
    #    print(row)

    #print("count")
    #for row in ex_csr.execute("select count(*) from temp_table_session6"):
    #    print(row)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # ---- ---- get from tables for yesterday, today, and tomorrow

    yestr = (ops_date - datetime.timedelta(days=1)).strftime("%Y%m%d")
    today = (ops_date                             ).strftime("%Y%m%d")
    tomor = (ops_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

    ora_tbls = "(SELECT * FROM TZ_" + yestr + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + today + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + tomor + "@ETMSREP) "

    # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

    qTracks = "SELECT fid, flight_index, acid, posit_time," + \
              " round(cur_lat/60.0,5)  as lat, " + \
              " round(cur_lon/-60.0,5) as lon  " + \
              " FROM " + ora_tbls + \
              " WHERE fid IN (select fid from temp_table_session6)" + \
              " AND point_status=-1 "

        # jan 12: " ORDER BY flight_index, posit_time"    # -- just to be sure

    if args_verbose: print(qTracks)

    #bb = elapsed.Elapsed()
    if (args_verbose):
        ora_df = pd.read_sql(qTracks, con=ex_conn)
        print(ora_df)
    else:

        ora_df = pd.read_sql(qTracks, con=ex_conn)

        #print("received")
    #bb.end("all lat,lons selected")

    #print("for-end")
    #for row in ex_csr.execute("select fid from temp_table_session6 where rownum < 10"):
    #    print(row)
    #print("count")
    #for row in ex_csr.execute("select count(*) from temp_table_session6"):
    #    print(row)

    # if args_verbose: print(ora_df)
    print("finished query oracle; found", len(ora_df), "tz reports")
    et.end("read tz from oracle")

    return(ora_df)

# =========================================================================

# Notes:
# Timezone aware datetime columns will be written as Timestamp with timezone
# type with SQLAlchemy if supported by the database. Otherwise, the datetimes
# will be stored as timezone unaware timestamps local to the original timezone.

from sqlalchemy import TIMESTAMP

def write_to_flight_level(fvf_df, verbose=False):

    tbl_name = "filed_vs_flown"   # note: lower case, otherwise:
    # sql.py:1336: UserWarning: The provided table name 'FLIGHT_LEVEL' is not
    # found exactly as such in the database

    if verbose: print("calling: to_sql()")

    # this doesn't seem to hurt...
    coltypes = {'DEP_TIME': TIMESTAMP,
                'ARR_TIME': TIMESTAMP}

    fvf_df.to_sql(tbl_name, sq_conn, if_exists='append', index=False,
                                     dtype=coltypes )

    print("done:", len(fvf_df))

    # print(conn.table_names())

