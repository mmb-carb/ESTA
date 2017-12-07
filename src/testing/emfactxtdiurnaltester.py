
from collections import defaultdict
from datetime import datetime as dt
import gzip
import numpy as np
import operator
import os
from src.core.date_utils import DOW, find_holidays
from src.core.eic_utils import eic_reduce, MAX_EIC_PRECISION
from src.core.output_tester import OutputTester
from src.emissions.emissions_table import EmissionsTable
from src.surrogates.calvadtemporalloader import CalvadTemporalLoader


class EmfacTxtDiurnalTester(OutputTester):

    KG_2_STONS = np.float32(0.001102310995)
    NUM_TESTED = 5
    POLLUTANTS = ['CO', 'NOX', 'SOX', 'TOG', 'PM', 'NH3']

    def __init__(self, config, position):
        super(EmfacTxtDiurnalTester, self).__init__(config, position)
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        self.by_region = self.config.getboolean('Output', 'by_region')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.region_names = dict((g, d['name']) for g,d in self.region_info.iteritems())
        self.original_profs = self._load_calvad_diurnal_profiles()
        # How many digits of EIC were preserved in the output files?
        self.precision = MAX_EIC_PRECISION
        if 'eic_precision' in self.config['Output']:
            self.precision = int(self.config['Output']['eic_precision'])
        # How many of the top EICs do we want to test?
        self.num_tested = EmfacTxtDiurnalTester.NUM_TESTED
        if 'num_tested' in self.config['Output']:
            self.num_tested = int(self.config['Output']['num_tested'])

    def test(self, emis, out_paths):
        ''' Master Testing Method.

            Compare the final NetCDF output file emissions to the original EMFAC2014 input files.
            PMEDS or CSE files will by compared by county, date, and EIC.

            emis format: emis.data[region][date string] = EmissionsTable
                             EmissionsTable[eic][poll] = value
        '''
        # Fail politely if not EIC14
        if self.precision != MAX_EIC_PRECISION:
            print('    + Output diurnal profiles can only be tested on EIC14 files.')
            return

        # Build top-emitting EIC list for all pollutants
        eics = EmfacTxtDiurnalTester.find_top_eics(emis)

        # test outputs for each dates
        for date in self.dates:
            d = date[5:]
            if d not in out_paths:
                print('    + No output text files found for testing on date: ' + d)
                continue
            cse_files = [f for f in out_paths[d] if f.rstrip('.gz').endswith('.cse')]
            pmeds_files = [f for f in out_paths[d] if f.rstrip('.gz').endswith('.pmeds')]
            if not pmeds_files and not cse_files:
                print('    + No output text files found for testing on date: ' + d)
                continue

            # find the day-of-week
            if date in find_holidays(self.base_year):
                dow = 'holi'
            else:
                by_date = str(self.base_year) + '-' + d
                dow = DOW[dt.strptime(by_date, self.date_format).weekday()]

            for file_path in pmeds_files:
                output_profs = self._output_pmeds_profiles(file_path, eics)
                self._write_profile_comparision(output_profs, date, dow)

            for file_path in cse_files:
                output_profs = self._output_cse_profiles(file_path, eics)
                self._write_profile_comparision(output_profs, date, dow)

    def _load_calvad_diurnal_profiles(self):
        """ Read the Calvad diurnal profiles file, and parse it into a collection, based on the
            day-of-week and region for each EIC.

            The original Calvad profiles will be in a dictionary with the form:
            calvad[region][dow][hr] = [ld, lm, hh, sbus]

            The new output profiles will be arranged like:
            profs[dow][region][eic] = np.zeros(24, dtype=np.float32)
        """
        # read the Calvad diurnal temporal profiles file
        ind = self.config.getlist('Surrogates', 'temporal_loaders').index('CalvadTemporalLoader')
        ctl = CalvadTemporalLoader(self.config, ind)
        orig_profs = ctl.load_diurnal(ctl.diurnal_path)

        # reorganize the data into something more useful for our individual EICs
        profs = {}
        for dow in set(DOW.values()):
            profs[dow] = {}
            for region in self.regions:
                profs[dow][region] = {}
                for eic in self.eic_info:
                    profs[dow][region][eic] = np.zeros(24, dtype=np.float32)
                    for hr in xrange(24):
                        profs[dow][region][eic][hr] = orig_profs[region][dow][hr][self.eic_info[eic][0]]

        return profs

    @staticmethod
    def find_top_eics(emis):
        """ We need a list of just the top-emitting EICs, so we can test a reasonable
            number of diurnal profiles.
            In particular, diurnal profiles are lost when emissions get very low,
            so we don't want to put noise in our testing by looking at low-emitting EICs.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        """
        # NOTE: this EmissionsTable object has backwards keys
        e = {}

        # organize the EICs by how much of each pollutant they comprise
        for region in emis.data:
            for date in emis.data[region]:
                for eic in emis.data[region][date]:
                    for poll, value in emis.data[region][date][eic].iteritems():
                        if poll not in e:
                            e[poll] = defaultdict(np.float32)
                        e[poll][eic] += value

        # find the largest EICs for each pollutant
        eics = set()
        for poll in e:
            eics.update(dict(sorted(e[poll].items(), key=operator.itemgetter(1),
                                    reverse=True)[:EmfacTxtDiurnalTester.NUM_TESTED]).keys())

        return eics

    def _output_pmeds_profiles(self, file_path, eics):
        ''' Look at the final output PMEDS file and build a dictionary of temporal profiles,
            by region, EIC, and pollutant.
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
        e = {}
        for line in lines:
            eic = int(line[22:36])
            if eic not in eics:
                continue
            region = int(line[71:73])
            hr = int(line[65:67]) % 24
            vals = [np.float32(v) if v else 0.0 for v in line[78:].rstrip().split(',')][:5]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = {}

            for i, val in enumerate(vals):
                if not val:
                    continue
                poll = self.POLLUTANTS[i]
                if poll not in e[region][eic]:
                    e[region][eic][poll] = np.zeros(24, dtype=np.float32)
                e[region][eic][poll][hr] += val

        return e

    def _output_cse_profiles(self, file_path, eics):
        ''' Look at the final output CSE file and build a dictionary of temporal profiles,
            by region, EIC, and pollutant.
            Line Format: SIC,EIC/SCC,I,J,REGION,YEAR,JUL_DAY,START_HR,END_HR,CO,NOX,SOX,TOG,PM,NH3
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
        e = {}
        for line in lines:
            ln = line.rstrip().split(',')
            eic = int(ln[1])
            if eic not in eics:
                continue
            region = int(ln[4])
            hr = int(ln[7]) % 24
            vals = [np.float32(v) if v else 0.0 for v in ln[9:15]]

            if region not in e:
                e[region] = {}
            if eic not in e[region]:
                e[region][eic] = {}

            for i, val in enumerate(vals):
                if not val:
                    continue
                poll = self.POLLUTANTS[i]
                if poll not in e[region][eic]:
                    e[region][eic][poll] = np.zeros(24, dtype=np.float32)
                e[region][eic][poll][hr] += val

        return e

    def _write_profile_comparision(self, output_profs, date, dow):
        """ Compare the temporal profiles in the output files to what they should be.

            Input profiles format:  profs[region][eic] = np.zeros(24, dtype=np.float32)
            Output profiles format:  profs[region][eic][poll] = np.zeros(24, dtype=np.float32)
        """
        # init output file
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'pmeds_diurnal_profiles_' + date + '.txt')
        f = open(file_path, 'w')
        f.write('NOTE: This file compares the diurnal profiles of ESTA output PMEDS files\n')
        f.write('      against the temporal profiles input to the model.\n')
        f.write('      Such tests break down if the emissions for a given Region/EIC are small.\n')

        # compare diurnal profiles by: Region, EIC, and pollutant
        for region, eic_data in output_profs.iteritems():
            for eic, poll_data in eic_data.iteritems():
                # write a section for a single Region / EIC combination
                max_diff = 0.000001
                min_total = 9.9e9    # arbitary large number
                in_prof = self.original_profs[dow][region][eic]
                body = ''

                # bulid total emissions for comparision
                for poll, hourly_emis in poll_data.iteritems():
                    body += 'OUTPUT_' + poll.ljust(4)[:4] + ',emis_kg,' + ','.join(['%.5f' % v for v in hourly_emis]) + '\n'

                # build output diurnal profiles lines
                for poll, hourly_emis in poll_data.iteritems():
                    total = sum(hourly_emis)
                    prof = [(v / total) for v in hourly_emis]
                    diff = max([abs(in_prof[i] - prof[i]) for i in xrange(24)])
                    if diff > max_diff:
                        max_diff = diff
                    if total < min_total:
                        min_total = total
                    body += 'OUTPUT_' + poll.ljust(4)[:4]  + ',profile,' + ','.join(['%.5f' % v for v in prof]) + '\n'
                # build input diurnal profile lines
                body += 'INPUT      ,profile,' + ','.join(['%.5f' % v for v in in_prof]) + '\n'

                # build a header line, with a QA flag
                header = '\n\n' + self.region_names[region] + ' - ' + str(eic) + ' - '
                if max_diff > 0.1 and min_total > 0.001:
                    header += 'QUESTIONABLE\n'
                elif max_diff > 0.01:
                    header += 'PROBABLY STILL OKAY\n'
                elif max_diff > 0.001:
                    header += 'CLOSE\n'
                elif max_diff > 0.0001:
                    header += 'QUITE CLOSE\n'
                elif max_diff > 0.00001:
                    header += 'NEARLY PERFECT\n'
                else:
                    header += 'PERFECT\n'

                # write the Region / EIC section to file
                f.write(header + body)

        f.close()
