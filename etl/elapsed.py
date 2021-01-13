
##############################################################################
#                         elpsed time                                        #
##############################################################################

import time
# calculate and printout elapsed times

class Elapsed:

    def __init__(self):
        self.start = time.time()

    def end(self, lbl):
        elapsed = time.time() - self.start
        mins    = int(elapsed / 60.0);  elapsed -= (mins * 60)
        secs    = int(elapsed % 60.0);  elapsed -= secs
        ms      = int(elapsed * 100)
        estr    = "%-20s: %dm %ds %dms" % (lbl, mins, secs, ms)
        print(estr)

