
import abc
from datetime import datetime


class EmissionsLoader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory
        self.date_format = self.config['Dates']['format']
        self.start_date = datetime.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = datetime.strptime(self.config['Dates']['end'], self.date_format)
        self.regions = self.config.parse_regions('Regions', 'regions')

    @abc.abstractmethod
    def load(self, emissions):
        return
