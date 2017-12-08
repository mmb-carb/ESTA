
from collections import defaultdict
from datetime import datetime as dt
import gzip
import numpy as np
import os
from src.core.date_utils import DOW, find_holidays
from src.core.eic_utils import eic_reduce, MAX_EIC_PRECISION
from src.core.output_tester import OutputTester
from src.emissions.emissions_table import EmissionsTable
from src.surrogates.calvadtemporalloader import CalvadTemporalLoader


class EmfacTxtTotalsTester(OutputTester):

    KG_2_STONS = np.float32(0.001102310995)
    POLLUTANTS = ['CO', 'NOX', 'SOX', 'TOG', 'PM', 'NH3']

    def __init__(self, config, position):
        super(EmfacTxtTotalsTester, self).__init__(config, position)
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        self.by_region = self.config.getboolean('Output', 'by_region')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.region_names = dict((g, d['name']) for g,d in self.region_info.iteritems())
        # How many digits of EIC were preserved in the output files?
        self.precision = MAX_EIC_PRECISION
        if 'eic_precision' in self.config['Output']:
            self.precision = int(self.config['Output']['eic_precision'])
        self.can_test_dow = True if self.precision == MAX_EIC_PRECISION else False
        self.eic_reduce = eic_reduce(str(self.precision))
        # read input day-of-week temporal profiles
        self.original_profs = self._load_dow_profiles()

    def test(self, emis, out_paths):
        ''' Master Testing Method.
            Compare the final NetCDF output file emissions to the original EMFAC2014 input files.
            PMEDS or CSE files will by compared by county, date, and EIC.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        '''
        # reduce input EIC precision, if necessary
        self._reduce_emissions_eics(emis)

        # loop through each date
        for d in self.dates:
            date = d[5:]
            if date not in out_paths:
                print('    + No output text files found for testing on date: ' + str(date))
                continue

            # find the day-of-week
            if date in find_holidays(self.base_year):
                dow = 'holi'
            else:
                by_date = str(self.base_year) + '-' + date
                dow = DOW[dt.strptime(by_date, self.date_format).weekday()]

            # test output pmeds, if any
            cse_files = [f for f in out_paths[date] if f.rstrip('.gz').endswith('.cse')]
            pmeds_files = [f for f in out_paths[date] if f.rstrip('.gz').endswith('.pmeds')]
            if pmeds_files or cse_files:
                self._read_and_compare_txt(pmeds_files, cse_files, date, emis, dow)

    def _load_dow_profiles(self):
        """ read the original Day-of-Week temporal profiles
            and convert them to a by-EIC and by-DOW format for easier use
        """
        try:
            # read the DOW temporal profiles file
            ind = self.config.getlist('Surrogates', 'temporal_loaders').index('CalvadTemporalLoader')
            ctl = CalvadTemporalLoader(self.config, ind)
            orig_profs = ctl.load_dow(ctl.dow_path)
        except ValueError:
            # some other temporal profiles were used, so we can't test thouse
            self.can_test_dow = False

        # reorganize the data into something more useful for our individual EICs
        profs = {}
        for dow in set(DOW.values()):
            profs[dow] = {}
            for region in self.regions:
                if self.can_test_dow:
                    profs[dow][region] = {}
                    for eic in self.eic_info:
                        profs[dow][region][eic] = orig_profs[region][dow][self.eic_info[eic][0]]
                else:
                    # unless it is EIC14, we can't apply day-of-week profiles to the outputs
                    profs[dow][region] = defaultdict(lambda: np.float32(1.0))

        return profs

    def _reduce_emissions_eics(self, emis):
        """ Sometimes the user will want to run ESTA in a reduced-EIC precision mode.
            In such cases, the output tests need to match their modeling goals.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        """
        if 'eic_precision' not in self.config['Output']:
            return
        elif self.config['Output']['eic_precision'] == MAX_EIC_PRECISION:
            return

        for region in emis.data:
            for date in emis.data[region]:
                e = EmissionsTable()
                for eic in emis.data[region][date]:
                    new_eic = self.eic_reduce(eic)
                    if new_eic not in e:
                        e[new_eic] = defaultdict(np.float32)
                    for poll, value in emis.data[region][date][eic].iteritems():
                        e[new_eic][poll] += value
                emis.data[region][date] = e

    def _read_and_compare_txt(self, pmeds, cse, date, emis, dow):
        ''' Read the output PMEDS files and compare the results with the
            input EMFAC2014 emissions.
        '''
        # sum up emissions in output PMEDS
        out_emis = {}
        for f in pmeds:
            out_emis = self._sum_output_pmeds(f, out_emis)
        for f in cse:
            out_emis = self._sum_output_cse(f, out_emis)

        # write the emissions comparison to a file
        if pmeds or cse:
            self._write_full_comparison(emis, out_emis, date, dow)

    def _write_full_comparison(self, emfac_emis, out_emis, d, dow):
        ''' Write a quick CSV to compare the EMFAC2014 and final output PMEDS.
            Write the difference by region, EIC, and pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        date = str(self.base_year) + '-' + d
        zero = np.float32(0.0)

        # init output file
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'pmeds_daily_totals_' + str(self.start_date.year)
                                 + '-' + d + '.txt')
        f = open(file_path, 'w')
        if not self.can_test_dow:
            f.write('Since your run is not by ' + str(MAX_EIC_PRECISION) + '-digit EIC, ' +
                    'your test results will not be adjust for day-of-week.\n\n')
        f.write('Region,EIC,Pollutant,EMFAC,OUTPUT,Percent Diff\n')

        # compare DOW profiles by: Region, EIC, and pollutant
        total_totals = {'emfac': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero, 'NH3': zero},
                        'final': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero, 'NH3': zero}}
        for region_num in self.regions:
            region_totals = {'emfac': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero, 'NH3': zero},
                             'final': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero, 'NH3': zero}}
            c = self.region_names[region_num]
            # write granular totals, by EIC
            eics = set(emfac_emis.get(region_num, date).keys() + out_emis[region_num].keys())
            for eic in eics:
                for poll in self.POLLUTANTS:
                    emfac = emfac_emis.get(region_num, date).get(eic, {}).get(poll.lower(), zero)
                    emfac *= self.original_profs[dow][region_num][eic]
                    final = out_emis.get(region_num, {}).get(eic, {}).get(poll, zero)
                    diff = EmfacTxtTotalsTester.percent_diff(emfac, final)
                    # fill region totals
                    region_totals['emfac'][poll] += emfac
                    region_totals['final'][poll] += final
                    if emfac < 0.00001 and final < 0.00001:
                        continue
                    # don't write the detailed line if there's no difference
                    if poll != 'NH3' and abs(diff) > 0.009999:
                        f.write(','.join([c, str(eic), poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')

            # write region totals, without EIC
            for poll in self.POLLUTANTS:
                # write line
                emfac = region_totals['emfac'][poll]
                final = region_totals['final'][poll]
                diff = EmfacTxtTotalsTester.percent_diff(emfac, final)
                f.write(','.join([c, 'TOTAL', poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')
                # build statewide totals
                total_totals['emfac'][poll] += emfac
                total_totals['final'][poll] += final

        # if more than one region, write state totals, without EIC
        if len(self.regions) > 1:
            for poll in self.POLLUTANTS:
                emfac = total_totals['emfac'][poll]
                final = total_totals['final'][poll]
                diff = EmfacTxtTotalsTester.percent_diff(emfac, final)
                if emfac < 0.00001 and final < 0.00001:
                    continue
                f.write(','.join(['TOTAL', 'TOTAL', poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')

        f.close()

    def _sum_output_pmeds(self, file_path, e):
        ''' Look at the final output PMEDS file and build a dictionary
            of the emissions by region and pollutant.
        '''
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rb')
            lines = f.readlines()
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
            lines = f.xreadlines()
        else:
            print('Emissions File Not Found: ' + file_path)
            return e

        # now that file exists, read it
        eic_limit = 1e13
        for line in lines:
            region = int(line[71:73])
            eic = int(line[22:36])
            if eic > eic_limit:
                eic = self.eic_reduce(eic)
            vals = [np.float32(v) if v else np.float32(0.0) for v in line[78:].rstrip().split(',')]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = dict(zip(self.POLLUTANTS, [np.float32(0.0)]*len(self.POLLUTANTS)))

            for i in xrange(6):
                e[region][eic][self.POLLUTANTS[i]] += vals[i] * self.KG_2_STONS

        return e

    def _sum_output_cse(self, file_path, e):
        ''' Look at the final output CSE file and build a dictionary
            of the emissions by region and pollutant.
            Format: SIC,EIC/SCC,I,J,REGION,YEAR,JUL_DAY,START_HR,END_HR,CO,NOX,SOX,TOG,PM,NH3
        '''
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rb')
            lines = f.readlines()
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
            lines = f.xreadlines()
        else:
            print('Emissions File Not Found: ' + file_path)
            return e

        # now that file exists, read it
        eic_limit = 1e13
        for line in lines:
            ln = line.rstrip().split(',')
            eic = int(ln[1])
            region = int(ln[4])
            if eic > eic_limit:
                eic = self.eic_reduce(eic)
            vals = [np.float32(v) if v else np.float32(0.0) for v in ln[9:15]]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = dict(zip(self.POLLUTANTS, [np.float32(0.0)]*len(self.POLLUTANTS)))

            for i in xrange(6):
                e[region][eic][self.POLLUTANTS[i]] += vals[i] * self.KG_2_STONS

        return e

    @staticmethod
    def percent_diff(a, b):
        ''' Find the percent difference of two numbers,
            and correctly trap the zero cases.
        '''
        if not a:
            if not b:
                return 0.0
            else:
                return -100.00

        return 100.0 * (a - b) / a
