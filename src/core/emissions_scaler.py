
import abc

class EmissionsScaler(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config
        self.new_emissions = None

    @abc.abstractmethod
    def scale(self, emissions, spatial_surr, temporal_surr):
        return None

    @staticmethod
    def parse_counties(counties_str):
        """ Parse the string we get back from the subareas field """
        if '..' in counties_str:
            counties = counties_str.split('..')
            counties = range(int(counties[0]), int(counties[1]))
        else:
            counties = [int(c) for c in counties_str.split()]

        return counties

    @staticmethod
    def normalize(lst):
        """ Normalize a flat list of floats, so that their sum equals 1.0. """
        total = sum(lst)
        return [val / total for val in lst]
