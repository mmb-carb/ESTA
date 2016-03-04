
import abc
from datetime import datetime as dt
from datetime import timedelta


class OutputTester(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.dates = self.config['Testing']['dates'].split()
        self.subareas = OutputTester.parse_subareas(self.config['Subareas']['subareas'])
        self.output_dirs = self.config['Output']['directories'].split()
        self.testing_dir = self.config['Testing']['testing_directory']

    def _find_dates_in_range(self):
        ''' Find all the dates in the modeling range,
            and return them as a list of strings in the run format.
            This method exists in case no testing dates are provided.
        '''
        d = dt(self.start_date.year, self.start_date.month, self.start_date.day)
        self.dates = [dt.strftime(d, self.date_format)]
        while d <= self.end_date:
            d += timedelta(days=1)
            self.dates.append(dt.strftime(d, self.date_format))

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
