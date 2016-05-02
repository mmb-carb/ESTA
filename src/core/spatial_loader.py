
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
    def parse_regions(regions_str):
        """ Parse the string we get back from the regions field """
        if '..' in regions_str:
            regions = regions_str.split('..')
            regions = range(int(regions[0]), int(regions[1]) + 1)
        else:
            regions = [int(c) for c in regions_str.split()]

        return regions
