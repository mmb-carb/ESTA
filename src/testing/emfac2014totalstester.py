
from datetime import datetime
from glob import glob
import gzip
from netCDF4 import Dataset
import os
import shutil
from src.core.output_tester import OutputTester
from src.core.eic_utils import eic_reduce
from src.core.spatial_loader import SpatialLoader


class Emfac2014TotalsTester(OutputTester):

    KG_2_STONS = 0.001102310995
    MOLSEC2STH = 0.003968316  # KG_2_STONS * 3600.0 / 1000.0
    SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
    POLLUTANTS = ['CO', 'NOX', 'SOX', 'TOG', 'PM']

    def __init__(self, config):
        super(Emfac2014TotalsTester, self).__init__(config)
        by_subarea = self.config['Output']['by_subarea'].lower()
        self.by_subarea = False if by_subarea in ['false', '0', 'no'] else True
        combine = self.config['Output']['combine_subareas'].lower()
        self.combine = False if combine in ['false', '0', 'no'] else True
        self.vtp2eic = eval(open(self.config['Misc']['vtp2eic'], 'r').read())
        self.county_names = eval(open(self.config['Misc']['county_names'], 'r').read())
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.emis_dirs = self.config['Emissions']['emissions_directories'].split()
        self.out_dirs = self.config['Output']['directories'].split()
        self.weight_file = ''
        self.groups = {}

    def test(self):
        ''' Master Testing Method. This method compares the final PMEDS/NetCDF output file emissions
            to the original EMFAC2014 input files.
            PMEDS files will by compared by county and date, but NetCDF files will only be compared
            by date.

            NOTE BENE: If the date tested is not a Tues/Wed/Thurs, the emissions will not be the
                       same as the EMFAC totals, as EMFAC represents only the "typical work day".
        '''
        # if no testing dates are provided, test all days in run
        if not self.dates:
            self._find_dates_in_range()

        # loop through each date
        for date in self.dates:
            dt = datetime.strptime(date, self.date_format)
            emis = {}

            # for each county
            for county_num in self.subareas:
                county = self.county_names[county_num]

                #   sum the input LDV EMFAC 2014 emissions
                ldv_file = self._find_emfac2014_ldv(dt, county)
                if not ldv_file:
                    continue
                emis[county_num] = self._read_emfac2014_ldv(ldv_file)

            # sum HDV EMFAC 2014 emissions
            hdv_file = self._find_emfac2014_hdv(dt, county)
            if not hdv_file:
                continue
            emis = self._read_emfac2014_hdv(hdv_file, emis)

            # test output pmeds, if any
            pmeds_files = self._find_output_pmeds(dt)
            if pmeds_files:
                self._read_and_compare_pmeds(pmeds_files, date, emis)

            # test output netcdf, if any
            ncf_files = self._find_output_ncf(dt)
            if ncf_files:
                self._read_and_compare_ncf(ncf_files, date, emis)

    def _read_and_compare_ncf(self, ncf_files, date, emis):
        ''' Read the output NetCDF files and compare the results with the
            input EMFAC2014 emissions.
        '''
        if not ncf_files:
            return

        # if NetCDF file exists, we need the weight file.
        self.weight_file = self.config['Output']['weight_file']

        # sum up emissions in output NetCDF
        out_emis = {}
        
        # load molecular weights file
        self._load_weight_file()
        for ncf_file in ncf_files:
            out_emis = self._sum_output_ncf(ncf_file, out_emis)

        # write the emissions comparison to a file
        self._write_general_comparison(date, emis, out_emis)

    def _read_and_compare_pmeds(self, pmeds_files, date, emis):
        ''' Read the output PMEDS files and compare the results with the
            input EMFAC2014 emissions.
        '''
        if not pmeds_files:
            return

        # sum up emissions in output PMEDS
        out_emis = {}
        for pmeds_file in pmeds_files:
            out_emis = self._sum_output_pmeds(pmeds_file, out_emis)

        # write the emissions comparison to a file
        self._write_full_comparison(date, emis, out_emis)

    def _write_general_comparison(self, date, emfac_emis, ncf_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output NetCDF.
            The NetCDF will only allow us to write the difference by pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'ncf_test_' + date + '.csv')
        f = open(file_path, 'w')
        f.write('Pollutant,EMFAC,NetCDF,Percent Diff\n')

        # create all-region EMFAC totals
        emfac_totals = {'CO': 0.0, 'NOX': 0.0, 'SOX': 0.0, 'TOG': 0.0, 'PM': 0.0}
        for subarea in self.subareas:
            if subarea not in emfac_emis:
                continue
            county_data = emfac_emis[subarea]
            for eic,eic_data in county_data.iteritems():
                for poll, value in eic_data.iteritems():
                    if poll.upper() in emfac_totals:
                        emfac_totals[poll.upper()] += value

        # find diff between EMFAC and NetCDF & add to file
        for poll in emfac_totals:
            emfac_value = emfac_totals[poll] * self.KG_2_STONS
            if poll not in ncf_emis:
                ncf_value = 0.0
                if emfac_value == 0.0:
                    diff = 0.0
                else:
                    diff = 100.00
            else:
                ncf_value = ncf_emis[poll]
                if emfac_value == 0.0:
                    diff = -100.0
                else:
                    diff = Emfac2014TotalsTester.percent_diff(emfac_value, ncf_emis[poll])

            line = [poll, str(emfac_value), str(ncf_value), '%.3f' % diff]
            f.write(','.join(line) + '\n')

        f.close()

    def _write_full_comparison(self, date, emis, out_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output PMEDS.
            Write the difference by county, EIC, and pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'pmeds_test_' + date + '.csv')
        f = open(file_path, 'w')
        f.write('County,EIC,Pollutant,EMFAC,PMEDS,Percent Diff\n')

        total_totals = {'emfac': {'CO': 0.0, 'NOX': 0.0, 'SOX': 0.0, 'TOG': 0.0, 'PM': 0.0},
                        'pmeds': {'CO': 0.0, 'NOX': 0.0, 'SOX': 0.0, 'TOG': 0.0, 'PM': 0.0}}
        for county_num in self.subareas:
            county_totals = {'emfac': {'CO': 0.0, 'NOX': 0.0, 'SOX': 0.0, 'TOG': 0.0, 'PM': 0.0},
                             'pmeds': {'CO': 0.0, 'NOX': 0.0, 'SOX': 0.0, 'TOG': 0.0, 'PM': 0.0}}
            c = self.county_names[county_num]
            # write granular totals, by EIC
            eics = set(emis[county_num].keys() + out_emis[county_num].keys())
            for eic in eics:
                for poll in self.POLLUTANTS:
                    # get data
                    emfac = emis.get(county_num, {}).get(eic, {}).get(poll, 0.0)
                    pmeds = out_emis.get(county_num, {}).get(eic, {}).get(poll, 0.0)
                    diff = Emfac2014TotalsTester.percent_diff(emfac, pmeds)
                    # fill county totals
                    county_totals['emfac'][poll] += emfac
                    county_totals['pmeds'][poll] += pmeds
                    # don't write the detailed line if there's no difference
                    if abs(diff) < 1.0e-3:
                        continue
                    diff = '%.3f' % diff
                    f.write(','.join([c, str(eic), poll, str(emfac), str(pmeds), diff]) + '\n')

            # write county totals, without EIC
            for poll in self.POLLUTANTS:
                # write line
                emfac = county_totals['emfac'][poll]
                pmeds = county_totals['pmeds'][poll]
                diff = Emfac2014TotalsTester.percent_diff(emfac, pmeds)
                diff = '%.3f' % diff
                f.write(','.join([c, 'TOTAL', poll, str(emfac), str(pmeds), diff]) + '\n')
                # build statewide totals
                total_totals['emfac'][poll] += emfac
                total_totals['pmeds'][poll] += pmeds

        # if more than one county, write state totals, without EIC
        if len(self.subareas) > 1:
            for poll in self.POLLUTANTS:
                emfac = total_totals['emfac'][poll]
                pmeds = total_totals['pmeds'][poll]
                diff = Emfac2014TotalsTester.percent_diff(emfac, pmeds)
                diff = '%.3f' % diff
                f.write(','.join(['TOTAL', 'TOTAL', poll, str(emfac), str(pmeds), diff]) + '\n')

        f.close()

    def _sum_output_pmeds(self, file_path, e):
        ''' Look at the final output PMEDS file and build a dictionary
            of the emissions by county and pollutant.
        '''
        county_nums = dict([(name[:8], i) for (i, name) in self.county_names.iteritems()])
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rb')
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
        else:
            print('Emissions File Not Found: ' + file_path)
            return e

        # now that file exists, read it
        for line in f.readlines():
            county = county_nums[line[:8].rstrip()]
            eic = int(line[22:36])
            vals = [float(v) if v else 0.0 for v in line[78:].rstrip().split(',')]

            if county not in e:
                e[county] = {}
            if eic not in e[county]:
                e[county][eic] = dict(zip(self.POLLUTANTS, [0.0]*len(self.POLLUTANTS)))

            for i in xrange(5):
                e[county][eic][self.POLLUTANTS[i]] += vals[i] * self.KG_2_STONS

        return e

    def _sum_output_ncf(self, file_path, e):
        ''' Look at the output NetCDF file and build a dictionary
            of the emissions by pollutant.
        '''
        # initialize emissions dictionary, if necessary
        for species in self.groups:
            group = self.groups[species]['group']
            if group not in e:
                e[group] = 0.0

        # open NetCDF file (if gzip, copy to temp file)
        if file_path.endswith('.gz'):
            unzipped_path = file_path[:-3]
            temp = open(unzipped_path, "wb")
            shutil.copyfileobj(gzip.open(file_path), temp)
            ncf = Dataset(unzipped_path, 'r')
        else:
            ncf = Dataset(file_path, 'r')

        # loop through each variable in NetCDF file
        sortedvar = sorted(ncf.variables)
        for species in sortedvar:
            if species == 'TFLAG':
                continue
            ems = ncf.variables[species][:24].sum() * self.MOLSEC2STH * self.groups[species]['weight']
            group = self.groups[species]['group']

            if group == 'NOX':
                e[group] += ems * self.groups['NO2']['weight'] / self.groups[species]['weight']
            elif group == 'SOX':
                e[group] += ems * self.groups['SO2']['weight'] / self.groups[species]['weight']
            else:
                # PM, TOG, CO, & NH3
                e[group] += ems

        ncf.close()
        if file_path.endswith('.gz'):
            os.remove(unzipped_path)
        return e

    def _load_weight_file(self):
        """ load molecular weight file
            File Format:
            NO          30.006      NOX    moles/s
            NO2         46.006      NOX    moles/s
            HONO        47.013      NOX    moles/s
        """
        # read molecular weight text file
        fin = open(self.weight_file,'r')
        lines = fin.read()
        fin.close()

        # read in CSV or Fortran-formatted file
        lines = lines.replace(',', ' ')
        lines = lines.split('\n')

        self.groups = {}
        # loop through file lines and
        for line in lines:
            # parse line
            columns = line.rstrip().split()
            if not columns:
                continue
            species = columns[0].upper()
            self.groups[species] = {}
            self.groups[species]['weight'] = float(columns[1])
            self.groups[species]['group'] = columns[2].upper()
            self.groups[species]['units'] = columns[3]

    def _find_output_pmeds(self, dt):
        ''' Find the output PMEDS file(s) for a given day. '''
        files = []
        if self.by_subarea and not self.combine:
            for odir in self.out_dirs:
                file_str = os.path.join(odir, '%02d' % dt.month, '%02d' % dt.day, '*.pmed*')
                possibles = glob(file_str)
                if possibles:
                    files += possibles
        else:
            date_str = str(dt.month) + 'd' + '%02d' % dt.day
            for odir in self.out_dirs:
                file_str = os.path.join(odir, 'pmeds', '*' + date_str + '*.pmed*')
                possibles = glob(file_str)
                if possibles:
                    files.append(possibles[0])

        return files

    def _find_output_ncf(self, dt):
        ''' Find the output NetCDF file(s) for a given day. '''
        files = []
        date_str = str(dt.year) + str(dt.month).zfill(2) + 'd' + str(dt.day)
        for odir in self.out_dirs:
            file_str = os.path.join(odir, 'ncf', '*' + date_str + '*')
            files += glob(file_str)

        return files

    def _find_emfac2014_ldv(self, dt, county):
        ''' Find a single county EMFAC2014 LDV emissions file for a given day. '''
        files = []
        for edir in self.emis_dirs:
            file_str = os.path.join(edir, '%02d' % dt.month, '%02d' % dt.day, 'emis', county + '.*')
            files += glob(file_str)

        if not files:
            print('\tERROR: EMFAC2014 LDV emissions file not found for county: ' + str(county) +
                  ', and date: ' + str(dt))
            return []

        return files[0]

    def _find_emfac2014_hdv(self, dt, county):
        ''' Find a single county EMFAC2014 HDV emissions file for a given day. '''
        season = 'summer' if dt.month in self.SUMMER_MONTHS else 'winter'
        files = []
        for edir in self.emis_dirs:
            file_str = os.path.join(edir, 'hd_' + season, 'emfac_hd_*.csv_all')
            files += glob(file_str)

        if not files:
            print('\tERROR: EMFAC2014 HDV emissions file not found for county: ' + str(county) +
                  ', and date: ' + str(dt))
            return []

        return files[0]

    def _read_emfac2014_ldv(self, file_path):
        """ Read an EMFAC2014 LDV CSV emissions file and colate the data into a table.
            File Format:
            year,month,sub_area,vehicle_class,process,cat_ncat,pollutant,emission_tons_day
            2031,7,Alpine (GBV),LDA,DIURN,CAT,TOG,0.000381882098646
            2031,7,Alpine (GBV),LDA,HOTSOAK,CAT,TOG,0.00171480645826
            2031,7,Alpine (GBV),LDA,PMBW,CAT,PM,0.00472484086652
        """
        e = {}

        # check that the file exists
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rb')
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
        else:
            print('\tERROR: LDV Emissions File Not Found: ' + file_path)
            return e

        # now that file exists, read it
        header = f.readline()
        for line in f.readlines():
            ln = line.strip().split(',')
            poll = ln[6].upper()
            if poll not in self.POLLUTANTS:
                continue
            v = ln[3]
            t = ln[5]
            if v == 'SBUS' and t == 'DSL':
                # There is no such thing as Light-Duty, Diesel School Busses.
                continue
            p = ln[4]
            eic = self.eic_reduce(self.vtp2eic[(v, t, p)])
            value = float(ln[-1])
            if value == 0.0:
                continue
            if eic not in e:
                e[eic] = dict(zip(self.POLLUTANTS, [0.0]*len(self.POLLUTANTS)))
            e[eic][poll] += value

        f.close()
        return e

    def _read_emfac2014_hdv(self, file_path, emis):
        """ Read an EMFAC2014 HD Diesel CSV emissions file and colate the data into a table
            File Format:
            2031,3,6.27145245709e-08,IDLEX,T6 CAIRP heavy,TOG
            2031,3,9.39715480515e-05,PMTW,T7 NNOOS,PM10
            2031,3,2.51918142645e-06,RUNEX,T7 POAK,SOx
        """
        # check that the file exists
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rb')
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
        else:
            print('\tERROR: Emissions File Not Found: ' + file_path)
            return emis

        # now that file exists, read it
        f = open(file_path, 'r')
        for line in f.readlines():
            ln = line.strip().split(',')
            poll = ln[-1].upper()
            if poll not in self.POLLUTANTS:
                continue
            value = float(ln[2])
            if value == 0.0:
                continue
            county = int(ln[1])
            v = ln[4]
            p = ln[3]
            eic = self.eic_reduce(self.vtp2eic[(v, 'DSL', p)])
            if county not in emis:
                emis[county] = {}
            if eic not in emis[county]:
                emis[county][eic] = dict(zip(self.POLLUTANTS, [0.0]*len(self.POLLUTANTS)))
            emis[county][eic][poll] += value

        f.close()
        return emis

    @staticmethod
    def percent_diff(a, b):
        ''' Find the percent difference of two numbers,
            and correctly trap the zero cases.
        '''
        if a == 0.0:
            if b == 0.0:
                return 0.0
            else:
                return -100.00

        return 100.0 * (a - b) / a
