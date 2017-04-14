from fconfig import Config as FConfig

class ttd(object):
    def __init__(self, basedir):
        self.config = FConfig(basedir)

    def run(self):

        from ttd.thr_manager import ThreadManager
        tm = ThreadManager()
        tm.start()


