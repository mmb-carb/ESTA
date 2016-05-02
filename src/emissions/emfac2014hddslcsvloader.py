
from collections import defaultdict
import gzip
import os
from emfac2014csvloader import Emfac2014CsvLoader
from emissions_table import EmissionsTable


class Emfac2014HdDslCsvLoader(Emfac2014CsvLoader):

    def __init__(self, config, directory, time_units):
        super(Emfac2014HdDslCsvLoader, self).__init__(config, directory, time_units)
        self.hd_ld = 'hd'

    def read_emfac_file(self, file_path):
        """ Read an EMFAC2014 HD Diesel CSV emissions file and colate the data into a table
            File Format:
            2031,3,6.27145245709e-08,IDLEX,T6 CAIRP heavy,TOG
            2031,3,9.39715480515e-05,PMTW,T7 NNOOS,PM10
            2031,3,2.51918142645e-06,RUNEX,T7 POAK,SOx
        """
        emis_by_region = {}

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
            if poll not in Emfac2014CsvLoader.VALID_POLLUTANTS:
                continue
            value = float(ln[2])
            if value == 0.0:
                continue
            region = int(ln[1])
            v = ln[4]
            p = ln[3]
            eic = self.vtp2eic[(v, 'DSL', p)]
            if region not in emis_by_region:
                emis_by_region[region] = EmissionsTable()
            emis_by_region[region][eic][poll] += value

        f.close()
        return emis_by_region
