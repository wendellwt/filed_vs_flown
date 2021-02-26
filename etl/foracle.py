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
sq_eng = create_engine(credentials, max_identifier_length=30)

# ======================================================================
# this doesn't seem to hurt...

with sq_eng.connect() as sq_con:

    sql_utc = "ALTER SESSION SET TIME_ZONE='UTC'"

    sq_con.execute(sql_utc)

# and do it for extr1 just because...
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

# get everything we can from oracle for flights to this ONE airport
#   for the ops day

import sys
import pytz
import code

make_utc = lambda t: t.replace(tzinfo=pytz.UTC)

def read_ops_day_data(ops_date, arr_apt, args_verbose):

    # ---- ---- get from tables for yesterday, today, and tomorrow

    yestr = (ops_date - datetime.timedelta(days=1)).strftime("%Y%m%d")
    today = (ops_date                             ).strftime("%Y%m%d")
    tomor = (ops_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

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
    apt_where = " = '" + arr_apt + "'"
    # OLD: get _all_ arrival airports (will be LOTS)
    #apt_where = " in ('" + "','".join(opsnet_45) + "') "

    sql = """SELECT acid, fid, flight_index, orig_time, source_type,
             dep_time, arr_time, dept_aprt, arr_aprt, acft_type, waypoints
FROM %s
WHERE %s
AND arr_aprt %s """ % (ora_tbls, arr_time, apt_where)

    # ORDER BY orig_time""" % (ora_tbls, arr_time, apt_where)

    if args_verbose: print(sql)

    ora_df = pd.read_sql(sql, con=ex_conn)

    #print("BEFORE pytz")
    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # ---- 3. make sure times are utc

    # Q: does this fixe the @#$%$%^& UTC issue???
    ora_df['DEP_TIME' ] = ora_df['DEP_TIME' ].map(make_utc)
    ora_df['ARR_TIME' ] = ora_df['ARR_TIME' ].map(make_utc)
    ora_df['ORIG_TIME'] = ora_df['ORIG_TIME'].map(make_utc)

    #print("AFTER pytz")
    #code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # if args_verbose: print(ora_df)

    return(ora_df)

# ########################################################################## #

# get all track points for all flights

def get_all_tz_using_temp(ops_date, fids, args_verbose):

    print("using temp to query oracle for all tz for ", len(fids), "fids")
    et = elapsed.Elapsed()

    ex_csr = cxo.Cursor(ex_conn)

    # if no create, is this needed???
    ex_csr.execute("delete from temp_table_session6")
    ex_conn.commit()

    # https://stackoverflow.com/questions/14904033/how-can-i-do-a-batch-insert-into-an-oracle-database-using-python
    # build rows for each date and add to a list of rows we'll use to insert as a batch
    rows = []
    for k in range(len(fids)):
        row = (fids[k],)
        rows.append(row)

    # insert all of the rows as a batch and commit
    ex_csr.prepare('insert into temp_table_session6 (fid) values (:FID)')
    ex_csr.executemany(None, rows)
    ex_conn.commit()

    # ---- ---- get from tables for yesterday, today, and tomorrow

    yestr = (ops_date - datetime.timedelta(days=1)).strftime("%Y%m%d")
    today = (ops_date                             ).strftime("%Y%m%d")
    tomor = (ops_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

    ora_tbls = "(SELECT * FROM TZ_" + yestr + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + today + "@ETMSREP UNION ALL " + \
                "SELECT * FROM TZ_" + tomor + "@ETMSREP) "

    # =========================================

    qTracks = "SELECT fid, flight_index, acid, posit_time," + \
              " round(cur_lat/60.0,5)  as lat, " + \
              " round(cur_lon/-60.0,5) as lon  " + \
              " FROM " + ora_tbls + \
              " WHERE fid IN (select fid from temp_table_session6)" + \
              " AND point_status=-1 "

        # jan 12: " ORDER BY flight_index, posit_time"

    if args_verbose: print(qTracks)

    ora_df = pd.read_sql(qTracks, con=ex_conn)

    if (args_verbose): print(ora_df)

    # and make sure these are utc also!
    ora_df['POSIT_TIME'] = ora_df['POSIT_TIME'].map(make_utc)

    et.end("read " + str(len(ora_df)) + " tz from oracle")
    return(ora_df)

# =========================================================================

def clean_oracle(opsday, ctr, verbose=False):

    with sq_eng.connect() as sq_con:

        #tbl_name = filed_vs_flown"   # note: lower case, otherwise:
        tbl_name = "TEST_FLIGHT_LEVEL.FILED_VS_FLOWN"

        sql_del = "DELETE FROM " + tbl_name + \
                  " WHERE opsday = to_date('" + opsday + "','YYYY-MM-DD') " + \
                  " AND artcc = '" + ctr + "' "

        if verbose: print(sql_del)

        code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        sq_con.execute(sql_del)
        print("executed???.")
        sq_con.commit(sql_del)

        print("deleted???.")
        code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # Q: need to do a commit here???

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

    # this doesn't seem to hurt...
    coltypes = {'DEP_TIME': TIMESTAMP,
                'ARR_TIME': TIMESTAMP}

    if verbose: print("calling: to_sql()")

    ora = elapsed.Elapsed()

    fvf_df.to_sql(tbl_name, sq_eng, if_exists='append', index=False,
                                     dtype=coltypes )

    # print("done:", len(fvf_df))
    # ora.end("wrote oracle:" + str(len(fvf_df)))

    # print(conn.table_names())

