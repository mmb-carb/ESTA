
import abc


class SpatialLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    @abc.abstractmethod
    def load(self, spatial_surrogates, temporal_surrogates):
        return None, None
