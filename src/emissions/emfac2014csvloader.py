
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
import gzip
import numpy as np
import os
import sys
from src.core.emissions_loader import EmissionsLoader
from emissions_table import EmissionsTable


class Emfac2014CsvLoader(EmissionsLoader):

    SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
    VALID_POLLUTANTS = ['NOX', 'CO', 'PM', 'SOX', 'TOG']
    DPM2PM = {'DPM10':'PM10', 'DPM25':'PM25', 'DPM':'PM'}
    PM2DPM = dict((v,k) for k,v in DPM2PM.iteritems())  # reverse lookup for DPM2PM
    REGION_CORRECTION = {'Riverside (MD/MDAQMD)':'Riverside (MDMDAQMD)', 'Riverside (MD/SCAQMD)':'Riverside (MDSCAQMD)'}

    def __init__(self, config, position):
        super(Emfac2014CsvLoader, self).__init__(config, position)
        time_units_list = self.config.getlist('Emissions', 'time_units')
        if position >= len(time_units_list):
            raise IndexError('Different number of emission loaders and time units.')
        self.time_units = time_units_list[position]
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.region_names = dict((g, d['name']) for g,d in self.region_info.iteritems())
        self.vtp2eic = self.config.eval_file('Emissions', 'vtp2eic')
        self.hd_ld = 'ld'
        self.config['Output']['dpmout'] = False
        try:
            self.dpm_polls = self.config.getlist('Output', 'dpm')
            self.config['Output']['dpmout'] = True
        except:
            pass
        # if running output DPM scenario, expand pollutant list
        if self.config['Output']['dpmout']:
            for pol in self.dpm_polls:
                # expand pollutant list to include DPM, DPM10, and DPM25, if needed
                if self.DPM2PM[pol] not in self.VALID_POLLUTANTS:
                    self.VALID_POLLUTANTS.append(self.DPM2PM[pol])

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
        elif self.time_units == 'daily_hd':
            return self.load_daily_hd(emissions)
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
        file_paths = os.path.join(self.directory, '%02d', '%02d', '%s.csv')
        today = deepcopy(self.base_start_date)
        while today <= self.base_end_date:
            for region in self.regions:
                #region_name = self.region_names[int(region)].split(' (')[0].replace(' ', '_')
                region_info = self.region_info[int(region)]
                region_name = '_'.join([region_info['county_name'], region_info['air_basin'], region_info['district']]).replace(' ','_')
                file_name = '_'.join([region_name, 'emission'])
                file_path = file_paths % (today.month, today.day, file_name)
                emissions.set(region, today.strftime(self.date_format),
                              self.read_emfac_file(file_path, region))
            today += timedelta(days=1)

        return emissions

    def load_daily_hd(self, emissions):
        file_paths = os.path.join(self.directory, '%02d', '%02d', 'emfac_hd.csv_all')
        today = deepcopy(self.base_start_date)
        while today <= self.base_end_date:
            file_path = file_paths % (today.month, today.day)

            emissions_by_region = self.read_emfac_file(file_path)
            for region in emissions_by_region:
                emissions.set(region, today.strftime(self.date_format),
                              emissions_by_region[region])
            today += timedelta(days=1)

        return emissions

    def load_seasonally(self, emissions):
        """ Read the seasonal EMFAC2014 CSV file and load them into the master emissions dictionary.
            This method is independent of LD/HD CSV file type.
        """
        file_paths = os.path.join(self.directory, self.hd_ld + '_%s',
                                  'emfac_' + self.hd_ld + '_%s.csv_all')
        print 'file_paths seasonally', file_paths
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

        today = deepcopy(self.base_start_date)
        while today <= self.base_end_date:
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
            today = deepcopy(self.base_start_date)
            month = -1
            while today <= self.base_end_date:
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
            print('    + Emissions File Not Found: ' + file_path)
            return e

        region_name = self.region_names[region]

        # now that file exists, read it
        header = f.readline()
        for line in f.readlines():
            ln = line.strip().split(',')
            # ln[0] --> calendar_year
            # ln[1] --> season_month
            # ln[2] --> sub_area
            # ln[3] --> vehicle_class
            # ln[4] --> fuel
            # ln[5] --> process
            # ln[6] --> cat_ncat
            # ln[7] --> pollutant
            # ln[8] --> emissions
            poll = ln[7].upper()
            if poll == 'PM2_5':
                poll = 'PM25'

            if poll not in Emfac2014CsvLoader.VALID_POLLUTANTS:
                continue
            if ln[2] != region_name:
                try:
                    self.REGION_CORRECTION[ln[2]]
                except:
                    continue
            v = ln[3]
            fuel_type = ln[4]
            t = ln[6]
            if v == 'SBUS' and t == 'DSL':
                # There is no such thing as Light-Duty, Diesel School Busses.
                continue
            p = ln[5]

            if fuel_type == 'Elec':
                t = fuel_type

            eic = self.vtp2eic[(v, t, p)]
            if eic not in self.eic_info:
                raise KeyError('eic_info file does not include the EIC: ' + str(eic))
            value = np.float32(ln[-1]) * np.float32(self.eic_info[eic][2])
            if value > 0.0:
                # output DPM scenario
                if self.config['Output']['dpmout']:
                    # check if eic_info.py has appended element for "is DPM eic?" (True/False)
                    try:
                        is_dpm_eic = self.eic_info[eic][3]
                    except:
                        sys.exit('\nERROR: "Run output DPM scenario?" is true, but eic_info file does not include "Is DPM eic?" field.\nCheck file: %s' % self.config['Surrogates']['eic_info'])
                    # map PM/PM10/PM2.5 to DPM/DPM10/DPM2.5 and aggregate emissions
                    if is_dpm_eic:
                        try:
                            dpmpoll = self.PM2DPM[poll]  # this can fail with non-DPM pollutants -> aggregate to criteria pollutant as normally done
                            # if DPM/DPM10/DPM2.5 has been identified in config file to output to ncf
                            if dpmpoll in self.dpm_polls:
                                e[eic][dpmpoll] += value

                            if poll == 'PM':  # Add DPM to PM
                                e[eic][poll] += value

                            elif poll == 'PM10':
                                e[eic][poll] += value

                            elif poll == 'PM25':
                                e[eic][poll] += value

                        # failed to map PM/PM10/PM2.5 to DPM/DPM10/DPM2.5 (pollutant is likely CO, TOG, NOX, SOX, etc.) --> aggregate to criteria pollutant as normally done
                        except:
                            e[eic][poll] += value
                    # not a DPM eic, therefore aggregate criteria pollutant as normally done 
                    else:
                        e[eic][poll] += value
                # regular scenario (should only involve criteria pollutants)
                else:
                    e[eic][poll] += value

        f.close()
        return e


class EMFAC2014EmissionsData(object):
    """ This class is designed as a helper to make organizing the huge amount of emissions
        information we pull out of the EMFAC2014 database easier.
        It is just a multiply-embedded dictionary with keys for things that we find in each file:
        region, date, and Emissions Data Tables.
        The date here should use the base year.
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
        """ standard Python helper to allow for str(x) and print(x) """
        return dict.__repr__(self.data).replace('dict', self.__class__.__name__, 1)
