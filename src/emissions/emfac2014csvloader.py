
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
import gzip
import os
from src.core.emissions_loader import EmissionsLoader
from emissions_table import EmissionsTable


class Emfac2014CsvLoader(EmissionsLoader):

    SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
    VALID_POLLUTANTS = ['nox', 'co', 'pm', 'sox', 'tog']

    def __init__(self, config, directory, time_units):
        super(Emfac2014CsvLoader, self).__init__(config, directory)
        self.time_units = time_units
        self.region_names = self.config.eval_file('Misc', 'region_names')
        self.vtp2eic = self.config.eval_file('Misc', 'vtp2eic')
        self.hd_ld = 'ld'

    def load(self, emissions):
        """ This is a general method to load emissions from EMFAC2014 result table-dumps in a
            simple CSV format. The first step is to determine the time-scale of the emissions.
        """
        # initialize emissions, if needed
        if not emissions:
            emissions = EMFAC2014EmissionsData()

        # load emissions for the correct time scale
        if self.time_units == 'daily':
            return self.load_daily(emissions)
        elif self.time_units == 'seasonally':
            return self.load_seasonally(emissions)
        elif self.time_units == 'monthly':
            return self.load_monthly(emissions)
        else:
            raise ValueError('EMFAC2014 emissions must be: daily, seasonally, or monthly.')

    def load_daily(self, emissions):
        """ Read the daily EMFAC2014 CSV file and load them into the master emissions dictionary.
            This method is independent of LD/HD CSV file type.
        """
        file_paths = os.path.join(self.directory, '%02d', '%02d', 'emis', '%s.csv')
        today = deepcopy(self.start_date)
        while today <= self.end_date:
            for region in self.regions:
                region_name = self.region_names[int(region)].split(' (')[0].replace(' ', '_')
                file_path = file_paths % (today.month, today.day, region_name)
                emissions.set(region, today.strftime(self.date_format),
                              self.read_emfac_file(file_path, region))
            today += timedelta(days=1)

        return emissions

    def load_seasonally(self, emissions):
        """ Read the seasonal EMFAC2014 CSV file and load them into the master emissions dictionary.
            This method is independent of LD/HD CSV file type.
        """
        file_paths = os.path.join(self.directory, self.hd_ld + '_%s',
                                  'emfac_' + self.hd_ld + '_%s.csv_all')
        days_by_season = self.find_days_by_season()
        for season, dates in days_by_season.iteritems():
            file_path = file_paths % (season, season)
            emissions_by_region = self.read_emfac_file(file_path)
            for date in dates:
                for region in emissions_by_region:
                    emissions.set(region, date.strftime(self.date_format),
                                  emissions_by_region[region])

        return emissions

    def find_days_by_season(self):
        """ A simple helper method to find all the days of interest in each season """
        days_by_season = defaultdict(list)

        today = deepcopy(self.start_date)
        while today <= self.end_date:
            season = 'summer' if today.month in Emfac2014CsvLoader.SUMMER_MONTHS else 'winter'
            days_by_season[season].append(deepcopy(today))
            today += timedelta(days=1)

        return days_by_season

    def load_monthly(self, emissions):
        """ Read the monthly EMFAC2014 CSV file and load them into the master emissions dictionary.
            This method is independent of LD/HD CSV file type.
        """
        file_paths = os.path.join(self.directory, '%02d', 'emis', '%s.csv')
        for region in self.regions:
            today = datetime(self.start_date.year, self.start_date.month, self.start_date.day)
            month = -1
            while today <= self.end_date:
                month = today.month
                file_path = file_paths % (month, region)
                emis = self.read_emfac_file(file_path, region)
                month_new = month
                while month_new == month:
                    emissions.set(region, today.strftime(self.date_format), emis)
                    today += timedelta(days=1)
                    month_new = today.month

        return emissions

    def read_emfac_file(self, file_path, region=0):
        """ Read an EMFAC2014 LDV CSV emissions file and colate the data into a table.
            File Format:
            year,month,sub_area,vehicle_class,process,cat_ncat,pollutant,emission_tons_day
            2031,7,Alpine (GBV),LDA,DIURN,CAT,TOG,0.000381882098646
            2031,7,Alpine (GBV),LDA,HOTSOAK,CAT,TOG,0.00171480645826
            2031,7,Alpine (GBV),LDA,PMBW,CAT,PM,0.00472484086652
        """
        e = EmissionsTable()

        # check that the file exists
        if os.path.exists(file_path + '.gz'):
            f = gzip.open(file_path + '.gz', 'rb')
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
        else:
            print('Emissions File Not Found: ' + file_path)
            return e

        region_name = self.region_names[region]

        # now that file exists, read it
        header = f.readline()
        for line in f.readlines():
            ln = line.strip().split(',')
            poll = ln[6].lower()
            if poll not in Emfac2014CsvLoader.VALID_POLLUTANTS:
                continue
            if ln[2] != region_name:
                continue
            v = ln[3]
            t = ln[5]
            if v == 'SBUS' and t == 'DSL':
                # There is no such thing as Light-Duty, Diesel School Busses.
                continue
            p = ln[4]
            eic = self.vtp2eic[(v, t, p)]
            value = float(ln[-1])
            if value == 0.0:
                continue
            e[eic][poll] += value

        f.close()
        return e


class EMFAC2014EmissionsData(object):
    """ This class is designed as a helper to make organizing the huge amount of emissions
        information we pull out of the EMFAC2014 database easier.
        It is just a multiply-embedded dictionary with keys for things that we find in each file:
        region, date, and Emissions Data Tables.
    """

    def __init__(self):
        self.data = {}

    def get(self, region, date):
        """ Getter method for EMFAC2014 Emissions Data dictionary """
        return self.data.get(region, {}).get(date, None)

    def set(self, region, date, table):
        """ Setter method for EMFAC2014 Emissions Data dictionary """
        # type validation
        if type(table) != EmissionsTable:
            raise TypeError('Only emission tables can be used in EMFAC2014EmissionsData.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if region not in self.data:
            self.data[region] = {}

        # add emissions
        if date not in self.data[region]:
            self.data[region][date] = table
        else:
            self.data[region][date].add_table(table)

    def __repr__(self):
        """ standard Python helper to allower for str(x) and print(x) """
        return dict.__repr__(self.data).replace('dict', self.__class__.__name__, 1)
