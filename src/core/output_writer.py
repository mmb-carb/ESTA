
import abc

class OutputWriter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, directory, time_units):
        self.config = config
        self.directory = directory
        self.time_units = time_units

    @abc.abstractmethod
    def write(self):
        return
