
import gzip
from netCDF4 import Dataset
import numpy as np
import os
import shutil
from src.core.output_tester import OutputTester


class EmfacNcfTotalsTester(OutputTester):

    KG_2_STONS = np.float32(0.001102310995)
    MOLESEC2KG = np.float32(3600.0) * KG_2_STONS
    POLLUTANTS = ['CO', 'NOX', 'SOX', 'TOG', 'PM']

    def __init__(self, config, position):
        super(EmfacNcfTotalsTester, self).__init__(config, position)
        self.weight_file = ''
        self.groups = {}

    def test(self, emis, out_paths):
        ''' Master Testing Method.
            Compare the final NetCDF output emissions to the original EMFAC2014 input files.
            NetCDF files can only be compared by date, not by region.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        '''
        # if no testing dates are provided, test all days in run
        if not self.dates:
            self._find_dates_in_range()

        # loop through each date, and test any output NetCDF
        for date in self.dates:
            ncf_files = [f for f in out_paths if f.rstrip('.gz').endswith('.ncf')]
            if ncf_files:
                self._read_and_compare_ncf(ncf_files, date, emis)

    def _read_and_compare_ncf(self, ncf_files, date, emis):
        ''' Read the output NetCDF files and compare the results with the
            input EMFAC2014 emissions.
        '''
        if not ncf_files or 'weight_file' not in self.config['Output']:
            return

        # if NetCDF file exists, we need the weight file.
        self.weight_file = self.config['Output']['weight_file']

        # sum up emissions in output NetCDF
        out_emis = {}
        self.groups = self.load_weight_file(self.weight_file)
        for ncf_file in ncf_files:
            out_emis = self._sum_output_ncf(ncf_file, out_emis)

        # write the emissions comparison to a file
        self._write_general_comparison(date, emis, out_emis)

    def _write_general_comparison(self, date, emfac_emis, ncf_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output NetCDF.
            The NetCDF will only allow us to write the difference by pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        zero = np.float32(0.0)
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'ncf_test_' + date + '.txt')
        f = open(file_path, 'w')
        f.write('NOTE: The EMFAC totals shown are not adjusted for day-of-week or diurnal ')
        f.write('profiles.\nAs such, they are most comparable for weekdays in Summer.\n\n')
        f.write('Pollutant,EMFAC,NetCDF,Percent Diff\n')

        # create all-region EMFAC totals
        emfac_totals = {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero}
        for region in self.regions:
            if region not in emfac_emis.data:
                continue
            region_data = emfac_emis.get(region, date)
            for eic_data in region_data.itervalues():
                for poll, value in eic_data.iteritems():
                    if poll.upper() in emfac_totals:
                        emfac_totals[poll.upper()] += value

        # find diff between EMFAC and NetCDF & add to file
        for poll in sorted(emfac_totals.keys()):
            emfac_val = emfac_totals[poll]
            ncf_val = ncf_emis.get(poll, 0.0)
            diff = EmfacNcfTotalsTester.percent_diff(emfac_val, ncf_val)
            f.write(','.join([poll, '%.5f' % emfac_val, '%.5f' % ncf_val, '%.2f' % diff]) + '\n')

        f.close()

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
            ems = ncf.variables[species][:24].sum() * self.MOLESEC2KG * self.groups[species]['weight']
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

    @staticmethod
    def load_weight_file(file_path):
        """ load molecular weight file
            File Format:
            NO          30.006      NOX    moles/s
            NO2         46.006      NOX    moles/s
            HONO        47.013      NOX    moles/s
        """
        # read molecular weight text file
        fin = open(file_path, 'r')
        lines = fin.read()
        fin.close()

        # read in CSV or Fortran-formatted file
        lines = lines.replace(',', ' ')
        lines = lines.split('\n')

        groups = {}
        # loop through file lines and
        for line in lines:
            # parse line
            columns = line.rstrip().split()
            if not columns:
                continue
            species = columns[0].upper()
            groups[species] = {}
            groups[species]['weight'] = np.float32(columns[1]) / np.float32(1000.0)
            groups[species]['group'] = columns[2].upper()
            groups[species]['units'] = columns[3]

        return groups

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
