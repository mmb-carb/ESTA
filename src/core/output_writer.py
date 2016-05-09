
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
        self.base_year = self.config.getint('Dates', 'base_year')
        self.regions = self.config.parse_regions('Regions', 'regions')

    @abc.abstractmethod
    def write(self):
        return
