
import abc
from datetime import datetime as dt


class EmissionsScaler(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, position):
        self.config = config
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = self.config.getint('Dates', 'base_year')
        self.regions = self.config.parse_regions('Regions', 'regions')

    @abc.abstractmethod
    def scale(self, emissions, spatial_surr, temporal_surr):
        """ Scale the emissions using spatial and temporal surrogates
            NOTE: This method should be a generator of emissions objects, otherwise it must
                  return a collection of emission objects.
        """
        while False:
            yield None
