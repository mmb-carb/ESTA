
import abc


class SpatialLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, position):
        self.config = config
        directories = self.config.getlist('Surrogates', 'spatial_directories')
        if position >= len(directories):
            raise IndexError('Different number of spatial loaders and directories.')
        self.directory = directories[position]

    @abc.abstractmethod
    def load(self, spatial_surrogates, temporal_surrogates):
        return None, None
