
import abc
from datetime import datetime as dt


class OutputTester(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.subareas = OutputTester.parse_subareas(self.config['Subareas']['subareas'])
        self.output_dirs = self.config['Output']['directories'].split()
        self.testing_dir = self.config['Testing']['testing_directory']

    @abc.abstractmethod
    def test(self):
        return

    @staticmethod
    def parse_subareas(subareas_str):
        """ Parse the string we get back from the subareas field """
        if '..' in subareas_str:
            subareas = subareas_str.split('..')
            subareas = range(int(subareas[0]), int(subareas[1]) + 1)
        else:
            subareas = [int(c) for c in subareas_str.split()]

        return subareas
