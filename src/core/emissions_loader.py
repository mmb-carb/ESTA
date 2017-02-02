
import abc
from datetime import datetime


class EmissionsLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, position):
        self.config = config
        directories = self.config.getlist('Emissions', 'emissions_directories')
        if position >= len(directories):
            raise IndexError('Different number of emission loaders and directories.')
        self.directory = directories[position]
        self.date_format = self.config['Dates']['format']
        self.start_date = datetime.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = datetime.strptime(self.config['Dates']['end'], self.date_format)
        self.regions = self.config.parse_regions('Regions', 'regions')
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')

    @abc.abstractmethod
    def load(self, emissions):
        return
