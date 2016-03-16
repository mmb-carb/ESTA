
from datetime import datetime
from glob import glob
import gzip
import io
import os
from src.core.output_tester import OutputTester
from src.core.eic_utils import eic_reduce


class Emfac2014TotalsTester(OutputTester):

    KG_2_STONS = 0.001102310995
    SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
    POLLUTANTS = ['co', 'nox', 'sox', 'tog', 'pm']

    def __init__(self, config):
        super(Emfac2014TotalsTester, self).__init__(config)
        by_subarea = self.config['Output']['by_subarea'].lower()
        self.by_subarea = False if by_subarea in ['false', '0', 'no'] else True
        self.vtp2eic = eval(open(self.config['Misc']['vtp2eic'], 'r').read())
        self.county_names = eval(open(self.config['Misc']['county_names'], 'r').read())
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.emis_dirs = self.config['Emissions']['emissions_directories'].split()
        self.out_dirs = self.config['Output']['directories'].split()
        self.qa_dir = self.config['Testing']['testing_directory']

    def test(self):
        ''' Master Testing Method. This method compares the final PMEDS output file emissions
            (aggregated by county and date) to the original EMFAC2014 input files.

            NOTE BENE: If the date tested is not a Tues/Wed/Thurs, the emissions will not be the
                       same as the EMFAC totals, as EMFAC represents only the "typical work day".
        '''
        # if no testing dates are provided, test all days in run
        if not self.dates:
            self._find_dates_in_range()
        
        # loop through each date
        for date in self.dates:
            dt = datetime.strptime(date, self.date_format)
            out_file = os.path.join([self.testing_dir,
                                     self.__class__.__name__ + '_' + date + '.csv'])
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

            # sum the final output PMEDS for the given day
            pmeds_files = self._find_output_pmeds(dt)
            if not pmeds_files:
                continue
            out_emis = {}
            for pmeds_file in pmeds_files:
                out_emis = self._sum_output_pmeds(pmeds_file, out_emis)

            # write the emissions comparison to a file
            self._write_emis_comparison(date, emis, out_emis)

    def _write_emis_comparison(self, date, emis, out_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output PMEDS.
            Write the difference by county, EIC, and pollutant.
            Don't print any numbers with zero percent difference.
        '''
        if not os.path.exists(self.qa_dir):
            os.mkdir(self.qa_dir)
        file_path = os.path.join(self.qa_dir, 'pmeds_test_' + date + '.csv')
        f = open(file_path, 'w')
        f.write('County,EIC,Pollutant,EMFAC,PMEDS,Percent Diff\n')

        total_totals = {'emfac': {'co': 0.0, 'nox': 0.0, 'sox': 0.0, 'tog': 0.0, 'pm': 0.0},
                        'pmeds': {'co': 0.0, 'nox': 0.0, 'sox': 0.0, 'tog': 0.0, 'pm': 0.0}}
        for county_num in self.subareas:
            county_totals = {'emfac': {'co': 0.0, 'nox': 0.0, 'sox': 0.0, 'tog': 0.0, 'pm': 0.0},
                             'pmeds': {'co': 0.0, 'nox': 0.0, 'sox': 0.0, 'tog': 0.0, 'pm': 0.0}}
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
            gz = gzip.open(file_path, 'rb')
            f = io.BufferedReader(gz)
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

    def _find_output_pmeds(self, dt):
        ''' Find a single output PMEDS file for a given day. '''
        files = []
        if self.by_subarea:
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

        if not files:
            print('\tERROR: Output PMEDS file not found: ' + file_str)
            return []

        return files
        

    def _find_emfac2014_ldv(self, dt, county):
        ''' Find a single county EMFAC2014 LDV emissions file for a given day. '''
        files = []
        for edir in self.emis_dirs:
            file_str = os.path.join(edir, '%02d' % dt.month, '%02d' % dt.day, 'emis', county + '.*')
            possibles = glob(file_str)
            if possibles:
                files.append(possibles[0])

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
            possibles = glob(file_str)
            if possibles:
                files.append(possibles[0])

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
            poll = ln[6].lower()
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
            poll = ln[-1].lower()
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
