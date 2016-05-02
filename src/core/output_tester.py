
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
        self.regions = OutputTester.parse_regions(self.config['Regions']['regions'])
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
    def parse_regions(regions_str):
        """ Parse the string we get back from the regions field """
        if '..' in regions_str:
            regions = regions_str.split('..')
            regions = range(int(regions[0]), int(regions[1]) + 1)
        else:
            regions = [int(c) for c in regions_str.split()]

        return regions
