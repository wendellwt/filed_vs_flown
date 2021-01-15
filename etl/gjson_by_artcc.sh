#!/bin/bash

# get arguments into useful vars

YMD=${1:-2020-01-10}
APT=${2:-DEN}
ARTCC=${3:-ZDV}
CORNER=${4:-ne}

# table names are  y_m_d, not y-m-d:
YMD=${YMD//-/_}

# and make output headers look nice
ALOWER=`echo $ARTCC | tr '[:upper:]' '[:lower:]'`

# ============================================================

export PGHOST="localhost"
export PGPORT=5432
export PGDATABASE="meekma"
export PGUSER="meow_user"

if [ -z "${PGPASSWORD}" ] ; then
    echo "you need to do this: export PGPASSWORD=putpasswordhere"
    exit 1
fi
# ============================================================


# -- %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# -- %%%%%%%%%%%%%%%%    common intersection & print funcs    %%%%%%%%%%%%%%%%%%%%%%
# --
# -- ============== length of intersection functions:
# --

psql --quiet << EOF
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

# not: echo querying sched, flown tables for: $YMD $APT $ARTCC

psql --quiet -t << EOF
--
-- ============== C is the artcc polygon to use
-- Notice: ST_Difference ONLY WORKS ON GEOGRAPHIES!!!!!!!!!!!!!!!!

-- Issue: I knew making everything a Geography would be a challenge.
--  1) convert ARTCC boundary to geometry
--  2) (assuming it is a parent tracon) get the position of the airport and convert to geometry
--  2a)  Transform that to a 'nice looking' crs, like one of the Lambert Conic Conformal ones
--  3) make a pretend tracon by making an ST_Buffer around that airport
--  4) finally, take the ST_Difference of the ARTCC geometry minus the tracon buffer geometry
--  6) cast it back to a Geography (is this needed???)

WITH C AS
-- the OLD way:
-- (SELECT boundary FROM centers WHERE name = '${ARTCC}'),

-- the NEW way:
(SELECT ST_Difference(
    (SELECT boundary::geometry from centers where name='${ARTCC}'),
    (SELECT ST_Transform(ST_Buffer(ST_Transform(position::geometry,26754),42*6076),4326) FROM airports WHERE ident='${APT}')
) as boundary),

--
-- ============== E is the SELECTion of acid, flight_index, and ZDV entry time of each flight
--
E AS (
  SELECT F.acid, F.flight_index,
         lower(period(atValue(tintersects(F.flown_path, C.boundary),TRUE))) as entry_time
  FROM
    C,
    (SELECT * FROM flown_fvf_${YMD} WHERE arr_apt='${APT}') F
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
--
-- gj: SELECT  S.acid, F.corner, S.flight_index, S.arr_time,
-- gj:  path_int_len(S.sched_path, C.boundary) as sched_dist_${ALOWER},
-- gj: path_int_len(trajectory(F.flown_path), C.boundary) as flown_dist_${ALOWER},
-- gj: path_int_diff_pct( trajectory(f.flown_path), S.sched_path, C.boundary) as pct
--
-- ============== main:
--
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(feature)
    )
FROM (
  SELECT jsonb_build_object(
    'type',       'Feature',
    'id',         gid,
    'geometry',   ST_AsGeoJSON(geom)::jsonb,
    'properties', to_jsonb(inputs) - 'gid' - 'geom'
  ) AS feature
  FROM (
  -- ===========================
  -- ==== sched part
( SELECT  'green' as color, F.acid, F.flight_index as gid, ST_Intersection(S.sched_path, C.boundary) as geom
FROM J,
     flown_fvf_${YMD} F,
     sched_fvf_${YMD} S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
AND   F.corner = '${CORNER}'
) UNION ALL (
  -- ==== flown part
SELECT  'blue' as color, F.acid, F.flight_index+1000000 as gid, ST_Intersection(trajectory(F.flown_path), C.boundary) as geom
FROM J,
     flown_fvf_${YMD} F,
     sched_fvf_${YMD} S,
     C
WHERE S.flight_index = J.flight_index
AND   S.orig_time    = J.sched_active_at
AND   F.flight_index = J.flight_index
AND   F.corner = '${CORNER}'
)
  -- ===========================
  ) inputs
) features;

EOF

