
import abc
from datetime import datetime as dt


class EmissionsLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, position):
        self.config = config
        directories = self.config.getlist('Emissions', 'emissions_directories')
        if position >= len(directories):
            raise IndexError('Different number of emission loaders and directories.')
        self.directory = directories[position]
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = self.config.getint('Dates', 'base_year')
        self.base_start_date = dt(self.base_year, self.start_date.month,  self.start_date.day)
        self.base_end_date = dt(self.base_year, self.end_date.month,  self.end_date.day)
        self.regions = self.config.parse_regions('Regions', 'regions')
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')

    @abc.abstractmethod
    def load(self, emissions):
        return
