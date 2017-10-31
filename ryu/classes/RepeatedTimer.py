from threading import Timer, Lock

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timers    = []
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
        self._timers.pop(0)
        self.lock.release()

    def start(self):
        self._timers.append(Timer(self.interval, self._run))
        self._timers[-1].start()

    def stop(self):
        for timer in self._timers:
            timer.cancel()
        for timer in self._timers:
            timer.join()
