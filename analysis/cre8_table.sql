
-- Feb 11 ORACLE table

CREATE TABLE "TEST_FLIGHT_LEVEL"."FILED_VS_FLOWN"
(
   ACID                  VARCHAR(14),
   ORIG                  VARCHAR(8),
   DEST                  VARCHAR(8),
   OPSDAY                DATE,
   CORNERPOST            VARCHAR(8),
   ARTCC_LEVEL           VARCHAR(8)
   LAST_FILED_DIST       NUMBER,
   BEFORE_ENTRY_DIST     NUMBER,
   FLOWN_DIST            NUMBER,
   LAST_FILED_UP_TO_DIST NUMBER,
   FLOWN_UP_TO_DIST      NUMBER,
   DEPT_TIME             TIMESTAMP WITH TIME ZONE,
   ARR_TIME              TIMESTAMP WITH TIME ZONE,
);

-- NOTE these are new:
   -- LAST_FILED_UP_TO_DIST NUMBER,
   -- FLOWN_UP_TO_DIST      NUMBER,


-- Feb 11 postgis on asdi-db
CREATE TABLE fvf_2020_03 (
    acid          text,
    fid           bigint,
    corner        text,
    artcc         text,
    dep_apt       text,
    arr_apt       text,
    flw_dist      float,
    b4_ent_dist   float,
    b4_dep_dist   float,

    b4_dep_up_to_dist  float,
    flw_up_to_dist     float,

    dep_time          timestamptz,
    arr_time          timestamptz,
    flw_geog          Geography,
    b4_ent_geog       Geography,
    b4_dep_geog       Geography,

    b4_dep_up_to_geog Geography,
    flw_up_to_geog    Geography
);

