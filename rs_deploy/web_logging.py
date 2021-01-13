
##############################################################################
#                            logger stuff                                    #
##############################################################################

# NOTE: file only, no console
# NOTE: fixed logging dir:

# setup:
#   $ mkdir -p /home/data/wturner/web_logs/
#   $ chmod a+rwx /home/data/wturner/web_logs/

# $ ll /home/data/wturner/web_logs/
# -rw-------. 1 rstudio-connect rstudio-connect 93 Dec 22 12:56 show_geosjon_20201222_0754.log

LOG_DIR="/home/data/wturner/web_logs/"

import os
import stat
import logging
import datetime

# c_loglevel = logging.INFO
f_loglevel = logging.DEBUG

lgr     = None

# ------------------------ setup logging

def setup_logger(filename_prefix, get_lgr):

    # use processing date in log filename in case two cron tasks start at once

    log_fn  = LOG_DIR + \
        filename_prefix + "_" + \
        datetime.datetime.today().strftime("%Y%m%d_%H%M") + \
        ".log"

        #"_proc_" + re.sub('-', '_', args.date) + \
    # -----

    # create a file handler
    f_handler = logging.FileHandler(log_fn)
    f_handler.setLevel(f_loglevel)

    # Create formatters and add it to handlers
    f_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')

    f_handler.setFormatter(f_format)

    # -----

    lgr = logging.getLogger(get_lgr)  # not sure where this shows up...
    lgr.setLevel(logging.DEBUG)

    # add the handlers to the logger
    lgr.addHandler(f_handler)

    # does it need ownner exec?
    # stat.S_IEXEC  |
    os.chmod( log_fn,
        stat.S_IREAD  |
        stat.S_IWRITE |
        stat.S_IRGRP  |
        stat.S_IWGRP  |
        stat.S_IROTH  |
        stat.S_IWOTH
    )

    return(lgr)


