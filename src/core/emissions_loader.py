
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
        self.subareas = EmissionsLoader.parse_subareas(self.config['Subareas']['subareas'])

    @abc.abstractmethod
    def load(self, emissions):
        return

    @staticmethod
    def parse_subareas(subareas_str):
        """ Parse the string we get back from the subareas field """
        if '..' in subareas_str:
            subareas = subareas_str.split('..')
            subareas = range(int(subareas[0]), int(subareas[1]))
        else:
            subareas = [int(c) for c in subareas_str.split()]

        return subareas

