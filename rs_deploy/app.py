#######################################################################
#             Flask web server that works with RConnect               #
#######################################################################

import sys
import psycopg2
from mobilitydb.psycopg import register
from geojson import Feature, FeatureCollection, dumps

from flask import Flask, render_template, request

sys.path.append('copied')  # stupid git/sharing  work-around
import get_paths
import fvf_by_artcc
import everything    # CATION: each of these makes a new PosgGreSQL connection
import web_logging

# --------------------------------------------------------------------

app = Flask(__name__)

# --------------------------------------------------------------------

lgr = web_logging.setup_logger("fvf", "helpme")

lgr.info("web app starting")

#######################################################################
#                     get request handlers                            #
#######################################################################

@app.route('/')

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
    use_pickle = False
    try:
        use_pickle = request.args['pckle']
    except:
        pass

    every_js = everything.get_everything(lgr, y_m_d, airport, center, use_pickle)

    lgr.info("get_everything - out")
    lgr.info("+++++")
    lgr.info(every_js)
    lgr.info("+++++")

    return every_js

#######################################################################
#                            main                                     #
#######################################################################

if __name__ == '__main__':
    app.run()

