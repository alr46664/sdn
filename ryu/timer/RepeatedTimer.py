from threading import Timer, Lock

from time import sleep, time
import random

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.lock       = Lock()
        self.start()

    def _run(self):
        self.lock.acquire()
        self.start()
        self.function(*self.args, **self.kwargs)
        self.lock.release()

    def start(self):
        self._timer = Timer(self.interval, self._run)
        # self._timer.daemon = True
        self._timer.start()

    def stop(self):
        if self._timer != None:
            self._timer.cancel()

def print_ok():
    s = random.random()*10
    print("Sleeping %.4f sec ..." % s)
    sleep(s)
    print("OK  -  time %s" %( time() ) )

try:
    r = RepeatedTimer(1, print_ok)
except(KeyboardInterrupt, SystemExit):
    r.stop()
