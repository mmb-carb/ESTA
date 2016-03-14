
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
        self.subareas = EmissionsScaler.parse_subareas(self.config['Subareas']['subareas'])

    @abc.abstractmethod
    def scale(self, emissions, spatial_surr, temporal_surr):
        """ Scale the emissions using spatial and temporal surrogates
            NOTE: This method should be a generator of emissions objects, otherwise it must
                  return a collection of emission objects.
        """
        while False:
            yield None

    @staticmethod
    def parse_subareas(subareas_str):
        """ Parse the string we get back from the subareas field """
        if '..' in subareas_str:
            subareas = subareas_str.split('..')
            subareas = range(int(subareas[0]), int(subareas[1]) + 1)
        else:
            subareas = [int(c) for c in subareas_str.split()]

        return subareas

    @staticmethod
    def normalize(lst):
        """ Normalize a flat list of floats, so that their sum equals 1.0. """
        total = sum(lst)
        return [val / total for val in lst]
