
from datetime import datetime
from glob import glob
import gzip
import os
from src.core.output_tester import OutputTester


class Emfac2014TotalsTester(OutputTester):

    SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
    POLLUTANTS = ['nox', 'co', 'pm', 'sox', 'tog']

    def __init__(self, config):
        super(Emfac2014TotalsTester, self).__init__(config)
        self.dates = list(self.config['Testing']['dates'])
        self.vtp2eic = eval(open(self.config['Misc']['vtp2eic'], 'r').read())
        self.county_names = eval(open(self.config['Misc']['county_names'], 'r').read())
        self.emis_dirs = self.config['Emissions']['emissions_directories']
        # TODO: Auto-find a good date, if one not provided

    def test(self):
        print('TODO: INCOMPLETE')
        return
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
                emis[county_num] = self._read_emfac2014_ldv(ldv_file)

            # sum HDV EMFAC 2014 emissions
            hdv_file = self._find_emfac2014_hdv(dt, county)
            emis = self._read_emfac2014_hdv(hdv_file, emis)

            # sum the final output PMEDS for the given day

            # write the emissions comparison to a file

    def _find_emfac2014_ldv(self, dt, county):
        ''' Find a single county EMFAC2014 LDV emissions file for a given day. '''
        files = []
        for edir in self.emis_dirs:
            files.append(glob(edir, str(dt.month), str(dt.day), 'emis', county + '.*'))

        if not files:
            print('ERROR: EMFAC2014 LDV emissions file not found', county, dt)

        return files[0]

    def _find_emfac2014_hdv(self, dt, county):
        ''' Find a single county EMFAC2014 HDV emissions file for a given day. '''
        season = self.SUMMER_MONTHS[dt.month]
        files = []
        for edir in self.emis_dirs:
            files.append(glob(edir, 'hd_' + season, 'emfac_hd_*.csv_all'))

        if not files:
            print('ERROR: EMFAC2014 HDV emissions file not found', county, dt)

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
        if os.path.exists(file_path + '.gz'):
            f = gzip.open(file_path + '.gz', 'rb')
        elif os.path.exists(file_path):
            f = open(file_path, 'r')
        else:
            print('Emissions File Not Found: ' + file_path)
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
            eic = self.vtp2eic[(v, t, p)]
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
        if os.path.exists(file_path):
            f = open(file_path, 'r')
        elif os.path.exists(file_path + '.gz'):
            f = gzip.open(file_path + '.gz', 'rb')
        else:
            exit('Emissions File Not Found: ' + file_path)

        # now that file exists, read it
        f = open(file_path, 'r')
        for line in f.readlines():
            ln = line.strip().split(',')
            poll = ln[-1].lower()
            if poll not in Emfac2014TotalsTester.VALID_POLLUTANTS:
                continue
            value = float(ln[2])
            if value == 0.0:
                continue
            county = int(ln[1])
            v = ln[4]
            p = ln[3]
            eic = self.vtp2eic[(v, 'DSL', p)]
            if county not in emis:
                emis[county] = {}
            if eic not in emis[county]:
                emis[county][eic] = dict(zip(self.VALID_POLLUTANTS, [0.0]*len(self.VALID_POLLUTANTS)))
            emis[county][eic][poll] += value

        f.close()
        return emis
