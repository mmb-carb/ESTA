
import abc
import os
from datetime import datetime as dt
from datetime import timedelta


class OutputTester(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config, position):
        self.config = config
        self.regions = self.config.parse_regions('Regions', 'regions')
        self.out_dir = self.config['Output']['directory']
        self.testing_dir = os.path.join(self.out_dir, 'qa')
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        if 'dates' in self.config['Testing']:
            self.dates = self.config['Testing']['dates'].split()
        else:
            self.dates = self._find_dates_in_range()

    def _find_dates_in_range(self):
        ''' Find all the dates in the modeling range,
            and return them as a list of strings in the run format.
            This method exists in case no testing dates are provided.
        '''
        d = dt(self.start_date.year, self.start_date.month, self.start_date.day)
        dates = [dt.strftime(d, self.date_format)]
        while d <= self.end_date:
            d += timedelta(days=1)
            dates.append(dt.strftime(d, self.date_format))
        
        return dates

    @abc.abstractmethod
    def test(self, emissions, output_paths):
        return
