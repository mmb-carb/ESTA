
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
        e = EmissionsTable()

        # check that the file exists
        if os.path.exists(file_path):
            f = open(file_path, 'r')
        elif os.path.exists(file_path + '.gz'):
            f = gzip.open(file_path + '.gz', 'rb')
        else:
            print('Emissions File Not Found: ' + file_path)
            return e

        # now that file exists, read it
        f = open(file_path, 'r')
        for line in f.readlines():
            ln = line.strip().split(',')
            poll = ln[-1].lower()
            if poll not in Emfac2014CsvLoader.VALID_POLLUTANTS:
                continue
            v = ln[4]
            p = ln[3]
            value = float(ln[2])
            e[(v, 'DSL', p)][poll] += value

        f.close()
        return e
