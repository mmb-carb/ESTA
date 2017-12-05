
import gzip
from netCDF4 import Dataset
import numpy as np
import os
import shutil
from src.core.output_tester import OutputTester


class EmfacNcfTotalsTester(OutputTester):

    MOLESEC2KG = np.float32(3600.0) * np.float32(0.000001102310995)

    def __init__(self, config, position):
        super(EmfacNcfTotalsTester, self).__init__(config, position)

    def test(self, emis, out_paths):
        ''' Master Testing Method.
            Compare the final NetCDF output emissions to the original EMFAC2014 input files.
            NetCDF files can only be compared by date, not by region.

            emis format: emis.data[region][date string] = EmissionsTable
                            EmissionsTable[eic][poll] = value
        '''
        # loop through each date, and test any output NetCDF
        for d in self.dates:
            date = d[5:]
            if date not in out_paths:
                print('    + No output NetCDF files found for testing on date: ' + str(date))
                continue
            ncf_files = [f for f in out_paths[date] if f.rstrip('.gz').endswith('.ncf')]
            if ncf_files:
                self._read_and_compare_ncf(ncf_files, date, emis)

    def _read_and_compare_ncf(self, ncf_files, date, emis):
        ''' Read the output NetCDF files and compare the results with the
            input EMFAC2014 emissions.
        '''
        if not ncf_files:
            return

        # sum up emissions in output NetCDF
        out_emis = {}
        for ncf_file in ncf_files:
            out_emis = self._sum_output_ncf(ncf_file, out_emis)

        # write the emissions comparison to a file
        self._write_general_comparison(date, emis, out_emis)

    def _write_general_comparison(self, d, emfac_emis, ncf_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output NetCDF.
            The NetCDF will only allow us to write the difference by pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        date = str(self.base_start_date.year) + '-' + d
        zero = np.float32(0.0)
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'ncf_daily_totals_' + str(self.start_date.year) +
                                 '-' + d + '.txt')
        f = open(file_path, 'w')
        f.write('NOTE: The EMFAC totals shown are not adjusted for temporal profiles.\n')
        f.write('      As such, they are most comparable for weekdays in Summer.\n\n')
        f.write('Pollutant,EMFAC,NetCDF,Percent Diff\n')

        # create all-region EMFAC totals
        emfac_totals = {'CO': zero, 'NOX': zero, 'SOX': zero, 'TOG': zero, 'PM': zero, 'NH3': zero}
        for region in self.regions:
            if region not in emfac_emis.data:
                continue
            region_data = emfac_emis.get(region, date)
            for eic_data in region_data.itervalues():
                for poll, value in eic_data.iteritems():
                    if poll.upper() in emfac_totals:
                        emfac_totals[poll.upper()] += value

        # find diff between EMFAC and NetCDF & add to file
        for poll in ['CO', 'NOX', 'SOX', 'TOG', 'PM', 'NH3']:
            emfac_val = emfac_totals[poll]
            ncf_val = ncf_emis.get(poll, 0.0)
            diff = EmfacNcfTotalsTester.percent_diff(emfac_val, ncf_val)
            f.write(','.join([poll, '%.5f' % emfac_val, '%.5f' % ncf_val, '%.2f' % diff]) + '\n')

        f.close()

    def _sum_output_ncf(self, file_path, e):
        ''' Look at the output NetCDF file and build a dictionary
            of the emissions by pollutant.
        '''
        # initialize emissions dictionary
        e = {'CO': 0.0, 'NH3': 0.0, 'NOX': 0.0, 'PM': 0.0, 'SOX': 0.0, 'TOG': 0.0}

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
            ems = ncf.variables[species][:24].sum() * self.MOLESEC2KG * self.EMFAC_WEIGHTS[species]['weight']
            group = self.EMFAC_WEIGHTS[species]['group']

            if group == 'NOX':
                e[group] += ems * self.EMFAC_WEIGHTS['NO2']['weight'] / self.EMFAC_WEIGHTS[species]['weight']
            elif group == 'SOX':
                e[group] += ems * self.EMFAC_WEIGHTS['SO2']['weight'] / self.EMFAC_WEIGHTS[species]['weight']
            else:
                # PM, TOG, CO, & NH3
                e[group] += ems

        ncf.close()
        if file_path.endswith('.gz'):
            os.remove(unzipped_path)
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

    # average species weight for EMFAC2014-type mobile-source species
    EMFAC_WEIGHTS = {'AACD': {'group': 'TOG', 'weight': 60.05},
                     'ACET': {'group': 'TOG', 'weight': 58.08},
                     'ACRO': {'group': 'TOG', 'weight': 56.06},
                     'ACYE': {'group': 'TOG', 'weight': 26.04},
                     'ALK1': {'group': 'TOG', 'weight': 30.07},
                     'ALK2': {'group': 'TOG', 'weight': 36.73},
                     'ALK3': {'group': 'TOG', 'weight': 58.61},
                     'ALK4': {'group': 'TOG', 'weight': 77.60},
                     'ALK5': {'group': 'TOG', 'weight': 118.89},
                     'APIN': {'group': 'TOG', 'weight': 136.23},
                     'ARO1': {'group': 'TOG', 'weight': 95.16},
                     'ARO2': {'group': 'TOG', 'weight': 118.72},
                     'B124': {'group': 'TOG', 'weight': 120.19},
                     'BACL': {'group': 'TOG', 'weight': 86.09},
                     'BALD': {'group': 'TOG', 'weight': 106.13},
                     'BDE13': {'group': 'TOG', 'weight': 54.09},
                     'BENZ': {'group': 'TOG', 'weight': 78.11},
                     'CCHO': {'group': 'TOG', 'weight': 44.05},
                     'CH4':  {'group': 'TOG', 'weight': 16.04},
                     'CO':   {'group': 'CO', 'weight': 28.01},
                     'CRES': {'group': 'TOG', 'weight': 108.14},
                     'ETHE': {'group': 'TOG', 'weight': 28.05},
                     'ETOH': {'group': 'TOG', 'weight': 46.07},
                     'FACD': {'group': 'TOG', 'weight': 46.03},
                     'GLY':  {'group': 'TOG', 'weight': 58.04},
                     'HCHO': {'group': 'TOG', 'weight': 30.03},
                     'HONO': {'group': 'NOX', 'weight': 47.013},
                     'IPRD': {'group': 'TOG', 'weight': 100.12},
                     'ISOP': {'group': 'TOG', 'weight': 68.12},
                     'MACR': {'group': 'TOG', 'weight': 70.09},
                     'MEK':  {'group': 'TOG', 'weight': 72.11},
                     'MEOH': {'group': 'TOG', 'weight': 32.04},
                     'MGLY': {'group': 'TOG', 'weight': 72.07},
                     'MVK':  {'group': 'TOG', 'weight': 70.09},
                     'MXYL': {'group': 'TOG', 'weight': 106.17},
                     'NH3':  {'group': 'NH3', 'weight': 17.03},
                     'NO':   {'group': 'NOX', 'weight': 30.006},
                     'NO2':  {'group': 'NOX', 'weight': 46.006},
                     'NROG': {'group': 'TOG', 'weight': 1.0},
                     'NVOL': {'group': 'TOG', 'weight': 1.0},
                     'OLE1': {'group': 'TOG', 'weight': 72.34},
                     'OLE2': {'group': 'TOG', 'weight': 75.78},
                     'OXYL': {'group': 'TOG', 'weight': 106.17},
                     'PACD': {'group': 'TOG', 'weight': 74.08},
                     'PAL':  {'group': 'PM', 'weight': 1.0},
                     'PCA':  {'group': 'PM', 'weight': 1.0},
                     'PCL':  {'group': 'PM', 'weight': 1.0},
                     'PEC':  {'group': 'PM', 'weight': 1.0},
                     'PFE':  {'group': 'PM', 'weight': 1.0},
                     'PK':   {'group': 'PM', 'weight': 1.0},
                     'PMC':  {'group': 'PM', 'weight': 1.0},
                     'PMG':  {'group': 'PM', 'weight': 1.0},
                     'PMN':  {'group': 'PM', 'weight': 1.0},
                     'PMOTHR': {'group': 'PM', 'weight': 1.0},
                     'PNA':    {'group': 'PM', 'weight': 1.0},
                     'PNCOM':  {'group': 'PM', 'weight': 1.0},
                     'PNH4': {'group': 'PM', 'weight': 1.0},
                     'PNO3': {'group': 'PM', 'weight': 1.0},
                     'POC':  {'group': 'PM', 'weight': 1.0},
                     'PRD2': {'group': 'TOG', 'weight': 116.16},
                     'PRPE': {'group': 'TOG', 'weight': 42.08},
                     'PSI':  {'group': 'PM', 'weight': 1.0},
                     'PSO4': {'group': 'PM', 'weight': 1.0},
                     'PTI':  {'group': 'PM', 'weight': 1.0},
                     'PXYL': {'group': 'TOG', 'weight': 106.17},
                     'RCHO': {'group': 'TOG', 'weight': 58.08},
                     'RNO3': {'group': 'TOG', 'weight': 147.18},
                     'SESQ': {'group': 'TOG', 'weight': 204.35},
                     'SO2':  {'group': 'SOX', 'weight': 64.059},
                     'SULF': {'group': 'SOX', 'weight': 80.058},
                     'TERP': {'group': 'TOG', 'weight': 136.23},
                     'TOLU': {'group': 'TOG', 'weight': 92.14},
                     '13BDE': {'group': 'TOG', 'weight': 54.09}}
