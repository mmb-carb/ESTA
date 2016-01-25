
from dtim4loader import Dtim4Loader
from src.core.temporal_loader import TemporalLoader


class Dtim4CalvadTemporalLoader(TemporalLoader):

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    def load(self, spatial_surrogates, temporal_surrogates):
        """ master method to load both day-of-week and diurnal CALVAD time profiles """
        if not temporal_surrogates:
            temporal_surrogates = {}

        # load DOW time profiles
        dow_file_path = self.config['Misc']['calvad_dow']
        temporal_surrogates['dow'] = self._load_dow(dow_file_path)

        # load diurnal time profiles
        diurnal_file_path = self.config['Misc']['calvad_diurnal']
        temporal_surrogates['diurnal'] = self._load_diurnal(diurnal_file_path)

        return temporal_surrogates

    def _load_diurnal(self, file_path):
        """ generate the diurnal temporal surrogates from the CalVad data
            hours range from 0 to 23
            days are 1, 2, 3, 6, 7, 8

            CalVad File Format:
            CNTY,DAY,HR,LD,LM,HH
            Alameda,1,00,0.020204,0.040504,0.060651
            Alameda,1,01,0.012772,0.038892,0.055813
        """
        calvad = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            # read line
            ln = line.strip().split(',')
            county = int(ln[0])
            dow = ln[1]
            hr = int(ln[2])
            ld = float(ln[3])
            lm = float(ln[4])
            hh = float(ln[5])

            # load data into surrogate
            if county not in calvad:
                calvad[county] = {}
            if dow not in calvad[county]:
                calvad[county][dow] = {}
            calvad[county][dow][hr] = [ld, lm, hh]

        f.close()

        return calvad

    def _load_dow(self, file_path):
        """ generate the DOW temporal surrogates from the CalVad data

            CalVad File Format:
            County_Number,FIPS,Day,DOW,LD,LM,HH
            1,1,1,sun,0.79679,0.495819,0.324035
            1,1,2,mon,0.948027,0.91867,0.893196
            1,1,3,tuth,1,1,1
        """
        calvad = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            # read line
            ln = line.strip().split(',')
            county = int(ln[0])
            dow = ln[3]
            ld = float(ln[4])
            lm = float(ln[5])
            hh = float(ln[6])

            # load data into surrogate
            if county not in calvad:
                calvad[county] = {}
            calvad[county][dow] = [ld, lm, hh]

        f.close()

        return calvad

