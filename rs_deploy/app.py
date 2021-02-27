#######################################################################
#             Flask web server that works with RConnect               #
#######################################################################

import sys
import psycopg2
from mobilitydb.psycopg import register
from geojson import Feature, FeatureCollection, dumps

from flask import Flask, render_template, request
from flask_compress import Compress
from flask_cors import cross_origin

sys.path.append('copied')  # stupid git/sharing  work-around
import get_paths
import fvf_by_artcc
import everything    # CAUTION: each of these makes a new PosgGreSQL connection
import get_feb20     # CAUTION: each of these makes a new PosgGreSQL connection
import web_logging

# --------------------------------------------------------------------
# compress:
# https://pypi.org/project/Flask-Compress/#:~:text=Flask%2DCompress%20allows%20you%20to,solve%20the%20problem%20for%20you.

app = Flask(__name__)
Compress(app)

# suggested response.headers.add('Access-Control-Allow-Origin', '*') here:
# https://gokhang1327.medium.com/separate-front-end-from-back-end-with-flask-ajax-a5b22b12d001

# --------------------------------------------------------------------

lgr = web_logging.setup_logger("fvf", "helpme")

lgr.info("web app starting")

#######################################################################
#                     get request handlers                            #
#######################################################################

@app.route('/')
@cross_origin()

def home():
    return render_template('index.html')

# -------------------------------------------------------------------

# let the_query = "get_geojsn?fn="  + filename;
# return GeoJson

@app.route('/get_geojson', methods=['GET'])

def do_something():

    filename = request.args['fn']

    gj_str = open(filename, 'r').read()

    return gj_str

# --------------------------------------------------------------------

@app.route('/get_kml', methods=['GET'])

def do_kml():
    filename = request.args['fn']
    kml_str = open(filename, 'r').read()
    return kml_str

# --------------------------------------------------------------------

@app.route('/get_fvf', methods=['GET'])

def do_fvf():

    lgr.info("get_fvf - in")

    bogus = request.args['apt']  # TODO! use this somehow

    paths_gj = get_paths.query_fvf(lgr, bogus )

    lgr.info("get_fvf - out")

    return paths_gj

# --------------------------------------------------------------------

@app.route('/get_CLT_ORD', methods=['GET'])

def do_CLT_ORD():

    lgr.info("get_CLT_ORD - in")

    bogus = request.args['apt']  # TODO! use this somehow

    paths_gj = get_paths.query_all(lgr, bogus )

    lgr.info("get_CLT_ORD - out")

    return paths_gj

# --------------------------------------------------------------------

@app.route('/get_summary', methods=['GET'])

def do_summary():

    lgr.info("get_summary - in")

    airport = request.args['apt']
    center = request.args['ctr']
    y_m_d = request.args['date']

    #sum_js = fvf_by_artcc.summarize_by_hour(lgr, airport, center, y_m_d)
    sum_js = fvf_by_artcc.summarize_by_corner(lgr, airport, center, y_m_d)

    lgr.info("get_summary - out")
    lgr.info("+++++")
    lgr.info(sum_js)
    lgr.info("+++++")

    return sum_js

# --------------------------------------------------------------------

@app.route('/get_everything', methods=['GET'])

# TODO: make sure json/encode/struct/decode is appropriate
# TODO: enable application/gzip compression!


def do_everything():

    lgr.info("get_everything - in")

    airport = request.args['apt']
    center = request.args['ctr']
    y_m_d = request.args['date']

    # don't need this now with csv reader
    # use_pickle = "false"
    #try:
    #    use_pickle = request.args['pckl']
    #    lgr.info("use_pickle:" + use_pickle)
    #except:
    #    lgr.info("use_pickle-except!")
    #    pass
    #lgr.info("use_pickle-val:" + use_pickle)

    #old: every_js = everything.get_everything(lgr, y_m_d, airport, center, use_pickle)
    every_js = everything.csv_to_geojson(lgr, y_m_d, airport, center)

    lgr.info("get_everything - out")
    #lgr.info("+++++")
    #lgr.info(every_js)
    #lgr.info("+++++")

    return every_js

# --------------------------------------------------------------------

import datetime

@app.route('/get_feb', methods=['GET'])
@cross_origin(origins="*/*")

def do_feb():

    lgr.info("get_feb - in")

    #airport = request.args['apt']
    center  = request.args['ctr']
    path    = request.args['pth']
    source  = request.args['src']
    gdate = datetime.datetime.strptime( request.args['date'], '%Y_%m_%d')

    lgr.info("get_feb - in.b:" + str(gdate))

    feb_js = get_feb20.get_postg_data_from_asdidb_f20(lgr, gdate, center, path, source)

    lgr.info("get_feb - out")
    #lgr.info("+++++")
    #lgr.info(feb_js)
    #lgr.info("+++++")

    return feb_js

#######################################################################
#                            main                                     #
#######################################################################

if __name__ == '__main__':
    app.run()

