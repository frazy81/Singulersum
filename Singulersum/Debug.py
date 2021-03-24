# 2021-03-13 ph Created
# 2021-03-17 ph enable logfiles

"""
    class Singulersum.Debug()

    class Debug implements different "timers" to detect performance bottlenecks and is the base class to implement debugging.
"""

import time

class Debug():

    start = time.time()
    logfile_name = None
    logfile_h = None

    def __init__(self):
        pass

    def logfile(self, file):
        Debug.logfile_name = file
        Debug.logfile_h = open(file, "wt")  # write text mode

    def debug(self, *kwargs, timeit=None):
        delta = time.time()-Debug.start
        elapsed = ""
        if timeit is not None:
            elapsed = timeit.stop()
            elapsed = "needed {:0.5f}s: ".format(elapsed)
        msg = ""
        for i in kwargs:
            msg += str(i)+" "
        print("[{:0.4f}s] {:s}".format(delta, elapsed+str(msg)))
        if Debug.logfile_name is not None:
            Debug.logfile_h.write("[{:0.4f}s] {:s}\n".format(delta, elapsed+str(msg)))

    def error(self, msg):
        self.debug("ERROR: "+str(msg))

    def timeit(self):
        return Timeit()

    def quit(self):
        if Debug.logfile_name is not None:
            self.debug("closing logfile '{:s}'".format(Debug.logfile_name))
            Debug.logfile_name=None
            Debug.logfile_h.close()

class Timeit():

    def __init__(self):
        self.start = time.time()

    def stop(self):
        self.stop = time.time()
        return self.diff()

    def diff(self):
        return self.stop-self.start
