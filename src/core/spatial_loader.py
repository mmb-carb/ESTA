
import abc


class SpatialLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    @abc.abstractmethod
    def load(self, spatial_surrogates, temporal_surrogates):
        return None, None

    @staticmethod
    def parse_subareas(subareas_str):
        """ Parse the string we get back from the subareas field """
        if '..' in subareas_str:
            subareas = subareas_str.split('..')
            subareas = range(int(subareas[0]), int(subareas[1]) + 1)
        else:
            subareas = [int(c) for c in subareas_str.split()]

        return subareas
