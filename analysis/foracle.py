#!/home/data/local/bin/python3.7

# ######################  oracle  #########################

import os
import cx_Oracle # as cxo
import pandas as pd

host     = os.environ.get('FLVL_IP')
port     = os.environ.get('FLVL_PORT')
service  = os.environ.get('FLVL_SERVICE')
username = os.environ.get('FLVL_USER')
password = os.environ.get('FLVL_PASS')

# ######################  oracle  #########################

fv_dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
fv_conn    = cx_Oracle.connect(username, password, fv_dsn_tns)

# =======================================================

def write_to_flight_level_BAD(fvf_df):

    tbl_name = "FILED_VS_FLOWN"

    print("about to write to oracle")

    fvf_df.to_sql(tbl_name, con=fv_conn, flavor='oracle')

    print("finished.")

# ######################  oracle + sqlalchemy  #########################

# import cx_Oracle
from sqlalchemy import types, create_engine

# conn = create_engine('oracle+cx_oracle://scott:tiger@host:1521/?service_name=hr')
credentials = 'oracle+cx_oracle://' + \
               username + ':' + password + '@' + host + ':' + port + \
              '/?service_name=' + service

# print(credentials)
conn = create_engine(credentials,
                     max_identifier_length=30)

def write_to_flight_level(fvf_df, verbose=False):

    tbl_name = "filed_vs_flown"   # note: lower case, otherwise:
    # sql.py:1336: UserWarning: The provided table name 'FILED_VS_FLOWN' is not
    # found exactly as such in the database

    if verbose: print("calling: to_sql()")

    fvf_df.to_sql(tbl_name, conn, if_exists='append', index=False)

    print("done:", len(fvf_df))

    # print(conn.table_names())

