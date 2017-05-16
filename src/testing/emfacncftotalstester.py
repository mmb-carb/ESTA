
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
        for date in self.dates:
            if date not in out_paths:
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

    def _write_general_comparison(self, date, emfac_emis, ncf_emis):
        ''' Write a quick CSV to compare the EMFAC2014 and final output NetCDF.
            The NetCDF will only allow us to write the difference by pollutant.
            NOTE: Won't print any numbers with zero percent difference.
        '''
        zero = np.float32(0.0)
        if not os.path.exists(self.testing_dir):
            os.mkdir(self.testing_dir)
        file_path = os.path.join(self.testing_dir, 'ncf_daliy_totals_' + date + '.txt')
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
    EMFAC_WEIGHTS = {'ACET': {'group': 'TOG', 'weight': 58.080294794111111},
                     'ACRO': {'group': 'TOG', 'weight': 56.065095857809517},
                     'ACYE': {'group': 'TOG', 'weight': 26.037175414675758},
                     'ALK1': {'group': 'TOG', 'weight': 30.069301786261089},
                     'ALK2': {'group': 'TOG', 'weight': 44.691406967680336},
                     'ALK3': {'group': 'TOG', 'weight': 71.35067688928892},
                     'ALK4': {'group': 'TOG', 'weight': 81.92575114621954},
                     'ALK5': {'group': 'TOG', 'weight': 119.87010167008739},
                     'APIN': {'group': 'TOG', 'weight': 136.23716650542266},
                     'ARO1': {'group': 'TOG', 'weight': 147.59053097679501},
                     'ARO2': {'group': 'TOG', 'weight': 125.26830693199521},
                     'B124': {'group': 'TOG', 'weight': 120.19247334798177},
                     'BALD': {'group': 'TOG', 'weight': 108.58968871387083},
                     'BDE13': {'group': 'TOG', 'weight': 54.104630365537083},
                     'BENZ': {'group': 'TOG', 'weight': 78.111907995314823},
                     'CCHO': {'group': 'TOG', 'weight': 44.053353836287314},
                     'CH4':  {'group': 'TOG', 'weight': 16.042013808472515},
                     'CO':   {'group': 'CO', 'weight': 28.01},
                     'CRES': {'group': 'TOG', 'weight': 148.19331323315282},
                     'ETHE': {'group': 'TOG', 'weight': 28.052612918918417},
                     'ETOH': {'group': 'TOG', 'weight': 46.068238797395125},
                     'GLY':  {'group': 'TOG', 'weight': 58.035858154296875},
                     'HCHO': {'group': 'TOG', 'weight': 30.025968928835287},
                     'HONO': {'group': 'NOX', 'weight': 47.013},
                     'IPRD': {'group': 'TOG', 'weight': 70.089276786978914},
                     'ISOP': {'group': 'TOG', 'weight': 68.194723934903479},
                     'MACR': {'group': 'TOG', 'weight': 70.092470649544524},
                     'MEK':  {'group': 'TOG', 'weight': 72.105521427766064},
                     'MEOH': {'group': 'TOG', 'weight': 32.042054730369934},
                     'MGLY': {'group': 'TOG', 'weight': 72.062141418457031},
                     'MVK':  {'group': 'TOG', 'weight': 80.856086967894754},
                     'MXYL': {'group': 'TOG', 'weight': 106.16479348682222},
                     'NH3':  {'group': 'NH3', 'weight': 17.03},
                     'NO':   {'group': 'NOX', 'weight': 30.006},
                     'NO2':  {'group': 'NOX', 'weight': 46.006},
                     'NROG': {'group': 'TOG', 'weight': 1.0},
                     'OLE1': {'group': 'TOG', 'weight': 69.9995},
                     'OLE2': {'group': 'TOG', 'weight': 69.12001900445847},
                     'OXYL': {'group': 'TOG', 'weight': 106.16406429835729},
                     'PACD': {'group': 'TOG', 'weight': 146.13996479674157},
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
                     'PRD2': {'group': 'TOG', 'weight': 105.70041936080648},
                     'PRPE': {'group': 'TOG', 'weight': 42.081045450483053},
                     'PSI':  {'group': 'PM', 'weight': 1.0},
                     'PSO4': {'group': 'PM', 'weight': 1.0},
                     'PTI':  {'group': 'PM', 'weight': 1.0},
                     'PXYL': {'group': 'TOG', 'weight': 106.16531054501606},
                     'RCHO': {'group': 'TOG', 'weight': 78.604},
                     'SO2':  {'group': 'SOX', 'weight': 64.059},
                     'SULF': {'group': 'SOX', 'weight': 80.058},
                     'TERP': {'group': 'TOG', 'weight': 136.23454891228528},
                     'TOLU': {'group': 'TOG', 'weight': 92.1377400026483}}
