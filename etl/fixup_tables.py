#!/home/data/local/bin/python3.7

import sys
import pandas as pd
import psycopg2
import argparse
import datetime

# ####################################################################### #
#                               argparse                                  #
# ####################################################################### #

corners_csv = "Arrival_Fixes_Lookup.csv"

parser = argparse.ArgumentParser(description="fixup flown table")

parser.add_argument('-d', '--date', default = datetime.date(2020, 1, 10),
            type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='start date yyyy-mm-dd')

parser.add_argument('-c', '--corners', type=str,
            help="name of corner csv file", default=corners_csv)

parser.add_argument('-v', '--verbose', action='store_const', const=True,
            help="verbosity", default=False )

args = parser.parse_args()

# ------------------------------------------------------------------------

# ---- and process args and adjust args to be in a nice format

sch_tbl = "sched_fvf_" + args.date.strftime("%Y_%m_%d")
flw_tbl = "flown_fvf_" + args.date.strftime("%Y_%m_%d")

# WORKS: stupid LookupError: unknown encoding: mbcs

f = open(args.corners, "r",  encoding="ascii")
cnr_df = pd.read_csv(f)

# =====================================================================

# note: d.b. access credentials are in dot files
pg_conn = psycopg2.connect(database='meekma')
pg_csr = pg_conn.cursor( )

# ########################################################################## #



# ########################################################################## #

def get_corners(apt):

    if args.verbose: print("arrival=", apt)
    clist = []

    for cdir in ('NE', 'SE', 'SW', 'NW'):

        try:
            fix = cnr_df.loc[(cnr_df['Airport']    == apt ) &
                             (cnr_df['Cornerpost'] == cdir)] \
                        .iloc[0]['Arrival Fix']

            clist.append( (cdir.lower(), fix) )
        except:
            # FIXME: an apt MAY NOT HAVE ALL 4 CORNERS!!!!!!!!!!!!!!!!!!!!!
            #print("cp NOT avail=", cdir)
            #return None
            continue

    return(clist)

# ############################## main ################################## #

# -- ============= SPECIAL: fixup sched table

try:
    sql  = """ALTER TABLE %s RENAME COLUMN geography TO sched_path; """ % sch_tbl
    if args.verbose: print(sql)
    pg_csr.execute(sql)
    pg_conn.commit()
except:
    if args.verbose: print("geography column already renamed?")
    pg_csr.execute("rollback")

# ========================================================================

# -- ============= ---- flown arrival airport

try:
    sql  = """ALTER TABLE %s ADD COLUMN arr_apt text; """ % flw_tbl
    if args.verbose: print(sql)
    pg_csr.execute(sql)
    pg_conn.commit()
except:
    if args.verbose: print("table already has arr_apt column?")
    pg_csr.execute("rollback")


sql  = """ UPDATE %s f
SET arr_apt = s.arr_apt
FROM %s s
WHERE s.flight_index = f.flight_index; """ % (flw_tbl, sch_tbl)

if args.verbose: print(sql)
pg_csr.execute(sql)
pg_conn.commit()

# -- ============= ---- flown departure airport

try:
    sql  = """ALTER TABLE %s ADD COLUMN dep_apt text; """ % flw_tbl
    if args.verbose: print(sql)
    pg_csr.execute(sql)
    pg_conn.commit()
except:
    print("table already has dep_apt column?")
    pg_csr.execute("rollback")


sql  = """ UPDATE %s f
SET dep_apt = s.dep_apt
FROM %s s
WHERE s.flight_index = f.flight_index; """ % (flw_tbl, sch_tbl)

if args.verbose: print(sql)
pg_csr.execute(sql)
pg_conn.commit()

# -- ============= ---- flown corner post
try:
    sql = "ALTER TABLE %s ADD COLUMN corner text;" % flw_tbl
    pg_csr.execute(sql)
    pg_conn.commit()
except:
    print("table already has dep_apt column?")
    pg_csr.execute("rollback")

sql = "CREATE TEMP TABLE corners (cp text, position Geography);"

if args.verbose: print(sql)
pg_csr.execute(sql)
pg_conn.commit()

airports = cnr_df.Airport.unique()

for arrival_airport in airports:
    print("arrival_airport=", arrival_airport)

    clist = get_corners(arrival_airport)

    if clist is None:
        continue  # something wrong, just go to next one

    sql = "DELETE FROM corners;"
    if args.verbose: print(sql)
    pg_csr.execute(sql)

    for d in clist:
        sql = "INSERT INTO corners VALUES ('%s', (select position from points where ident='%s'));" % d
        if args.verbose: print(sql)
        pg_csr.execute(sql)

    sql = """UPDATE %s
    SET corner = ( SELECT cp FROM corners
               ORDER BY corners.position <-> flown_path
               LIMIT 1)  WHERE arr_apt='%s';""" % (flw_tbl, arrival_airport)

    if args.verbose: print(sql)
    pg_csr.execute(sql)

pg_conn.commit()
