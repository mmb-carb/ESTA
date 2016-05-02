
import abc
from datetime import datetime as dt


class EmissionsScaler(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.regions = EmissionsScaler.parse_regions(self.config['Regions']['regions'])

    @abc.abstractmethod
    def scale(self, emissions, spatial_surr, temporal_surr):
        """ Scale the emissions using spatial and temporal surrogates
            NOTE: This method should be a generator of emissions objects, otherwise it must
                  return a collection of emission objects.
        """
        while False:
            yield None

    @staticmethod
    def parse_regions(regions_str):
        """ Parse the string we get back from the regions field """
        if '..' in regions_str:
            regions = regions_str.split('..')
            regions = range(int(regions[0]), int(regions[1]) + 1)
        else:
            regions = [int(c) for c in regions_str.split()]

        return regions

    @staticmethod
    def normalize(lst):
        """ Normalize a flat list of floats, so that their sum equals 1.0. """
        total = sum(lst)
        return [val / total for val in lst]
