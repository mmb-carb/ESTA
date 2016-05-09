
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
        self.regions = self.config.parse_regions('Regions', 'regions')
        self.output_dirs = self.config.getlist('Output', 'directories')
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
