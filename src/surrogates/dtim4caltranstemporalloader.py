
from dtim4loader import Dtim4Loader
from src.core.temporal_loader import TemporalLoader


class Dtim4CaltransTemporalLoader(TemporalLoader):

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    def load(self, spatial_surrogates, temporal_surrogates):
        """ master method to generate the temporal surrogates needed to scale EMFAC2014 emissions
            There are two kinds of temporal surrogates here:
            (1) Diurnal Surrogates from DTIM4
            (2) DOW surrogates from CalTrans

            CalTrans File Format:
            County_Number,FIPS,Day,DOW,LD,LM,HH
            1,1,1,sun,0.79679,0.495819,0.324035
            1,1,2,mon,0.948027,0.91867,0.893196
            1,1,3,tuth,1,1,1
        """
        file_path = self.config['Misc']['caltrans_factors']

        caltrans = {}
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
            if county not in caltrans:
                caltrans[county] = {}
            caltrans[county][dow] = [ld, lm, hh]

        # load dow surrogate
        f.close()
        temporal_surrogates['dow'] = caltrans

        return temporal_surrogates
