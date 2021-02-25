
# some utility routines to make geojson/FC out of portions of a df
# that were deemed interesting

import json
import code
import datetime
from shapely.geometry import mapping

# #######################################################################

def output_json_to_file(center_df, ctr, artcc_shp, y_m_d):

    # for TESTING, get rid of most extra columns
    # and keep ALL of the WITHIN ones

    print("+++++++++++++++")
    print(center_df.columns)
    print("+++++++++++++++")

    trim_df = center_df.drop(['FID', 'DEP_TIME',
  #'ACID',
  'FID',
  #'FLIGHT_INDEX',
  'DEP_TIME',
  'ARR_TIME',
  'DEPT_APRT',
  'ARR_APRT',
  #'corner',
  #'OPSDAY',
  #'artcc',
  'ACFT_TYPE',

    # these don't exist yet
  #'scheduled_upto_dist',
  #'first_filed_upto_dist',
  #'last_filed_upto_dist',
  #'flown_upto_dist',

    # these are the interesting ones, keep them
  #'scheduled_within_dist',
  #'first_filed_within_dist',
  #'last_filed_within_dist',
  #'at_entry_within_dist',
  #'flown_within_dist',

    # these don't exist yet
  #'scheduled_upto_path',
  #'first_filed_upto_path',
  #'last_filed_upto_path',
  #'flown_upto_path'
                              ], axis=1)

    help_output_corner(trim_df, 'ne', ctr, artcc_shp, y_m_d)

    # today just tracking down one acid, so don't want/need these:
    # help_output_corner(trim_df, 'se', ctr, artcc_shp, y_m_d)
    # help_output_corner(trim_df, 'sw', ctr, artcc_shp, y_m_d)
    # help_output_corner(trim_df, 'nw', ctr, artcc_shp, y_m_d)

    code.interact(local=locals())   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# =========================================================================

def help_output_corner(trim_df, cnr, ctr, artcc_shp, y_m_d):

    ne_df = trim_df.loc[trim_df['corner']==cnr]

    # HELP >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #ne_15z_df = ne_df.loc[ne_df['ARR_TIME'] >= datetime.datetime(2020,3,2,15,0,0)]
    ne_15z_df = ne_df.loc[ne_df['ACID'] == 'SWA3421']

    # ==== method 1. write GeoDataFrame to disk (meaning paths only)
    # <<<<<<<<<<<<<<<<<<< LAME
    # ne_15z_gf = gpd.GeoDataFrame( ne_15z_df, geometry='flw_path')
    # ne_15z_gf.rename( {'geometry' : 'flw_path'}, axis=1, inplace=True)
    # fn = "cnr_" + cnr + ".gjsn"
    # ne_15z_gf.to_file(fn, driver="GeoJSON")
    # print("fn=", fn)
    # <<<<<<<<<<<<<<<<<<< LAME

    # ==== method 2. add colors, and FC including artcc

    if len(ne_15z_df) == 0:   # empty === uninteresting
        return

    paths_gj = form_feature_collection(ne_15z_df, artcc_shp)

    fn = "files/fc_" + cnr + '_' + ctr + '_' + y_m_d + ".gjsn"

    with open(fn, "w") as fd:
        fd.write( json.dumps(paths_gj) )

    print("fn=", fn)

# ====================================================================

from geojson import Feature, FeatureCollection

# note: input is a df, not a gf

def form_feature_collection(flts_df, artcc_shp):

    features = [ Feature(geometry   = mapping(artcc_shp),
                         id         = 1,
                         properties = { "name" : 'ARTCC'}
                        ), ]
    help_id = 4

    for index, row in flts_df.iterrows():

        # http://geojson.tools/ shows colors from properties:
        # make paths for these:
        for P in [ ( 'scheduled_within_path',   'red'),
                   ( 'first_filed_within_path', 'green'),
                   ( 'last_filed_within_path',  'orange'),
                  # not yet: ( 'at_entry_within_path',    ''),
                   ( 'flown_within_path',       'black'),   ]:

            foo_feat = Feature(geometry   = mapping(row[P[0]]),
                           id         = help_id,
                           properties =
                                 { "acid"    : row['ACID'],
                                   "corner"  : row['corner'],
                                   "color"   : P[1],
                                   "path"    : P[0],
                                   #"arr_time" : row['arr_time'].replace(' ','T'),
                                 })

            features.append(foo_feat)
            help_id += 1

    feature_collection = FeatureCollection(features)
    return(feature_collection)

