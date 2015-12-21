
import abc

class SpatialLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, directory):
        self.directory = directory

    @abc.abstractmethod
    def load(self):
        return
