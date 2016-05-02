
import abc
from datetime import datetime as dt


class OutputWriter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, directory, time_units):
        self.config = config
        self.directory = directory
        self.time_units = time_units
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.regions = OutputWriter.parse_regions(self.config['Regions']['regions'])

    @abc.abstractmethod
    def write(self):
        return

    @staticmethod
    def parse_regions(regions_str):
        """ Parse the string we get back from the regions field """
        if '..' in regions_str:
            regions = regions_str.split('..')
            regions = range(int(regions[0]), int(regions[1]) + 1)
        else:
            regions = [int(c) for c in regions_str.split()]

        return regions
