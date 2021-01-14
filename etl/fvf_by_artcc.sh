#!/bin/bash

# get arguments into useful vars

YMD=${1:-2019-06-02}
APT=${2:-DEN}
ARTCC=${3:-ZDV}

# table names are  y_m_d, not y-m-d:
YMD=${YMD//-/_}

# and make output headers look nice
ALOWER=`echo $ARTCC | tr '[:upper:]' '[:lower:]'`

# ============================================================

export PGHOST="localhost"
export PGPORT=5432
export PGDATABASE="meekma"
export PGUSER="meow_user"
export PGPASSWORD="1575eyest"

# ============================================================


# -- %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# -- %%%%%%%%%%%%%%%%    common intersection & print funcs    %%%%%%%%%%%%%%%%%%%%%%
# --
# -- ============== length of intersection functions:
# --

psql << EOF
CREATE OR REPLACE FUNCTION path_int_len(geography, geography) RETURNS numeric AS \$\$
        BEGIN
             RETURN round((ST_Length(ST_Intersection(\$1, \$2)) / 1852)::decimal,1);
        END;
\$\$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION path_int_diff_pct(geography, geography, geography) RETURNS numeric AS \$\$
        BEGIN
             -- div by 0; a/c flew through center but sched didn't
             IF ST_Length(ST_Intersection(\$2, \$3)) = 0 THEN
                 RETURN 0;
             ELSE
                 RETURN (round((ST_Length(ST_Intersection(\$1, \$3))*100.0 /
                                ST_Length(ST_Intersection(\$2, \$3)))::decimal,1) );
             END IF;
        END;
\$\$ LANGUAGE plpgsql;
EOF


# -- $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

echo querying sched, flown tables for: $YMD $APT $ARTCC
psql << EOF
--
-- ============== E is the acid, flight_index, and ZDV entry time of each flight
--
WITH E AS (
  SELECT F.acid, F.flight_index, lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    (SELECT * FROM flown_fvf_${YMD} WHERE arr_apt='${APT}') F,
    (SELECT boundary FROM centers WHERE name = '${ARTCC}') C
  WHERE intersects(F.flown_path, C.boundary) ),
--
-- ============== J is the SELECTion of the scheduled path previous to artcc entry time
--
    J AS (
  SELECT S.acid, S.flight_index, E.entry_time, max(S.orig_time) as sched_active_at
  FROM E,
       sched_fvf_${YMD} S
  WHERE S.flight_index = E.flight_index
  AND   S.orig_time < E.entry_time
  GROUP BY S.acid, S.flight_index, E.entry_time
)
--
-- ============== main:
--
SELECT  S.acid, F.corner, S.flight_index, S.arr_time,
  path_int_len(S.sched_path, C.boundary) as sched_dist_${ALOWER},
  path_int_len(trajectory(F.flown_path), C.boundary) as flown_dist_${ALOWER},
  path_int_diff_pct( trajectory(f.flown_path), S.sched_path, C.boundary) as pct
FROM J,
     flown_fvf_${YMD} F,
     sched_fvf_${YMD} S,
     (SELECT boundary FROM centers WHERE name = '${ARTCC}') C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
ORDER BY F.corner, pct;

EOF

