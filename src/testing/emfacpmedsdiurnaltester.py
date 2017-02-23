
from collections import defaultdict
import gzip
import numpy as np
import operator
import os
from src.core.eic_utils import eic_reduce, MAX_EIC_PRECISION
from src.core.output_tester import OutputTester
from src.emissions.emissions_table import EmissionsTable


class EmfacPmedsDiurnalTester(OutputTester):

    NUM_TESTED = 5  # TODO: Should be optionally configurable
    KG_2_STONS = np.float32(0.001102310995)
    POLLUTANTS = ['CO', 'NOX', 'SOX', 'TOG', 'PM']

    def __init__(self, config, position):
        super(EmfacPmedsDiurnalTester, self).__init__(config, position)
        self.by_region = self.config.getboolean('Output', 'by_region')
        self.region_names = self.config.eval_file('Misc', 'region_names')
        self.precision = MAX_EIC_PRECISION
        if 'eic_precision' in self.config['Output']:
            self.precision = int(self.config['Output']['eic_precision'])

    def test(self, emis, out_paths):  # TODO: Deal with this being a new OutputFiles object
        ''' Master Testing Method.

            TODO: read outputs, read profiles, compare for ~10 biggest EICs

            Compare the final NetCDF output file emissions to the original EMFAC2014 input files.
            PMEDS files will by compared by county, date, and EIC.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        '''
        # Fail politely if not PMEDS
        pmeds_files = [f for f in out_paths if f.rstrip('.gz').endswith('.pmeds')]
        if not pmeds_files:
            print('    + Output diurnal profiles can only be tested on PMEDS files.')
            return

        # Fail politely if not EIC14
        if self.precision != MAX_EIC_PRECISION:
            print('    + Output diurnal profiles can only be tested on EIC14 files.')
            return

        # Build top-emitting EIC list for all pollutants
        eics = EmfacPmedsDiurnalTester.find_top_eics(emis)

        # TODO: The out_paths given do not have dates attached............................................................................................
        # TODO: Overhaul esta_model.py *again* to pass dates along with files.................................................

        # TODO: read output files. Need by region: hourly profiles, total emis
        # TODO: read Calvad hourly profiles
        # TODO: print comparison: date,region,EIC,which,total_emis,0,1,...,23

    @staticmethod
    def find_top_eics(emis):
        """ TODO

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        """
        # NOTE: this EmissionsTable object has backwards keys
        e = EmissionsTable()
        # organize the EICs by how much of each pollutant they comprise
        for region in emis.data:
            for date in emis.data[region]:
                for eic in emis.data[region][date]:
                    for poll, value in emis.data[region][date][eic].iteritems():
                        if poll not in e:
                            e[poll] = defaultdict(np.float32)
                        e[poll][eic] += value

        # find the largest EICs for each pollutant
        eics.set()
        for poll in e:
            eics.update(dict(sorted(e[poll].items(), key=operator.itemgetter(1),
                                    reverse=True)[:NUM_TESTED]).keys())

        return eics

    def _output_pmeds_profiles(self, file_path, e):
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
            vals = [np.float32(v) if v else 0.0 for v in line[78:].rstrip().split(',')]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = dict(zip(self.POLLUTANTS, [0.0]*len(self.POLLUTANTS)))

            for i in xrange(5):
                e[region][eic][self.POLLUTANTS[i]] += vals[i] * self.KG_2_STONS

        return e

    def old(self):
        # reduce input EIC precision, if necessary
        self._reduce_emissions_eics(emis)

        # if no testing dates are provided, test all days in run
        if not self.dates:
            self._find_dates_in_range()

        # loop through each date
        for date in self.dates:
            # test output pmeds, if any
            pmeds_files = [f for f in out_paths if f.rstrip('.gz').endswith('.pmeds')]
            if pmeds_files:
                self._read_and_compare_txt(pmeds_files, date, emis)

    def _reduce_emissions_eics(self, emis):
        """ Sometimes the user will want to run ESTA in a reduced-EIC precision mode.
            In such cases, the output tests need to match their modeling goals.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        """
        if 'eic_precision' not in self.config['Output'] or self.config['Output']['eic_precision'] == '14':
            return

        for region in emis.data:
            for date in emis.data[region]:
                e = EmissionsTable()
                for eic in emis.data[region][date]:
                    new_eic = self.eic_reduce(eic)
                    for poll, value in emis.data[region][date][eic].iteritems():
                        if new_eic not in e:
                            e[new_eic] = defaultdict(np.float32)
                        e[new_eic][poll] += value
                emis.data[region][date] = e

    def _read_and_compare_txt(self, files, date, emis):
        ''' Read the output PMEDS files and compare the results with the
            input EMFAC2014 emissions.
        '''
        # sum up emissions in output PMEDS
        out_emis = {}
        for f in files:
            out_emis = self._sum_output_pmeds(f, out_emis)

        # write the emissions comparison to a file
        if files:
            self._write_full_comparison(date, emis, out_emis)

    # TODO: This logic looks ugly in the final output file if the config file is set to EIC3: Reduce to EIC3?
    def _write_full_comparison(self, date, emfac_emis, out_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output PMEDS.
            Write the difference by region, EIC, and pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        zero = np.float32(0.0)
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'pmeds_test_' + date + '.txt')
        f = open(file_path, 'w')
        f.write('NOTE: The EMFAC totals shown are not adjusted for day-of-week or diurnal ')
        f.write('profiles.\nAs such, they are most comparable for weekdays in Summer.\n\n')
        f.write('Region,EIC,Pollutant,EMFAC,PMEDS,Percent Diff\n')

        total_totals = {'emfac': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero},
                        'final': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero}}
        for region_num in self.regions:
            region_totals = {'emfac': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero},
                             'final': {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero}}
            c = self.region_names[region_num]
            # write granular totals, by EIC
            eics = set(emfac_emis.get(region_num, date).keys() + out_emis[region_num].keys())
            for eic in eics:
                for poll in self.POLLUTANTS:
                    emfac = emfac_emis.get(region_num, date).get(eic, {}).get(poll.lower(), zero)
                    final = out_emis.get(region_num, {}).get(eic, {}).get(poll, zero)
                    diff = EmfacPmedsDiurnalTester.percent_diff(emfac, final)
                    # fill region totals
                    region_totals['emfac'][poll] += emfac
                    region_totals['final'][poll] += final
                    # don't write the detailed line if there's no difference
                    if abs(diff) > 1.0e-3:
                        f.write(','.join([c, str(eic), poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')

            # write region totals, without EIC
            for poll in self.POLLUTANTS:
                # write line
                emfac = region_totals['emfac'][poll]
                final = region_totals['final'][poll]
                diff = EmfacPmedsDiurnalTester.percent_diff(emfac, final)
                f.write(','.join([c, 'TOTAL', poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')
                # build statewide totals
                total_totals['emfac'][poll] += emfac
                total_totals['final'][poll] += final

        # if more than one region, write state totals, without EIC
        if len(self.regions) > 1:
            for poll in self.POLLUTANTS:
                emfac = total_totals['emfac'][poll]
                final = total_totals['final'][poll]
                diff = EmfacPmedsTotalsTester.percent_diff(emfac, final)
                f.write(','.join(['TOTAL', 'TOTAL', poll, '%.5f' % emfac, '%.5f' % final, '%.2f' % diff]) + '\n')

        f.close()

    def _sum_output_pmeds_OLD(self, file_path, e):
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
            vals = [np.float32(v) if v else 0.0 for v in line[78:].rstrip().split(',')]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = dict(zip(self.POLLUTANTS, [0.0]*len(self.POLLUTANTS)))

            for i in xrange(5):
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
