
import os
import numpy as np
from src.core.temporal_loader import TemporalLoader


class FlexibleTemporalLoader(TemporalLoader):

    def __init__(self, config, position):
        super(FlexibleTemporalLoader, self).__init__(config, position)
        self.dow_path = os.path.join(self.directory, self.config['Surrogates']['temporal_dow'])
        diurnal_file = self.config['Surrogates']['temporal_diurnal']
        self.diurnal_path = os.path.join(self.directory, diurnal_file)

    def load(self, spatial_surrogates, temporal_surrogates):
        """ master method to load both day-of-week and diurnal time profiles """
        if not temporal_surrogates:
            temporal_surrogates = {}

        # load DOW time profiles
        temporal_surrogates['dow'] = FlexibleTemporalLoader.load_dow(self.dow_path)

        # load diurnal time profiles
        temporal_surrogates['diurnal'] = FlexibleTemporalLoader.load_diurnal(self.diurnal_path)

        return temporal_surrogates

    @staticmethod
    def load_diurnal(file_path):
        """ generate the diurnal temporal surrogates from the CSV file
            (hours must range from 0 to 23)

            Example File Format:
            REGION,DAY,HR,LD,LM,HH,SBUS
            Alameda,sun,00,0.020204,0.040504,0.060651,0.0
            Alameda,sun,01,0.012772,0.038892,0.055813,0.0
        """
        surrs = {}
        f = open(file_path, 'r')
        labels = f.readline().rstrip().split(',')[3:]
        for line in f.xreadlines():
            # read line
            ln = line.rstrip().split(',')
            region = int(ln[0])
            dow = ln[1]
            hr = int(ln[2])
            if hr < 0 or hr > 23:
                raise ValueError('Hour in Diurnal CSV outside valid range 0 to 23: ' + ln[2])
            values = [np.float32(val) for val in ln[3:]]

            # make sure the surrogate structure is ready
            if region not in surrs:
                surrs[region] = {}
            if dow not in surrs[region]:
                surrs[region][dow] = [dict((l, np.float32(0.0)) for l in labels) for _ in xrange(24)]

            # load data into surrogate
            for i, val in enumerate(values):
                surrs[region][dow][hr][labels[i]] = val

        f.close()
        return surrs

    @staticmethod
    def load_dow(file_path):
        """ generate the DOW temporal surrogates from the CSV file

            Example File Format:
            REGION,Day,DOW,LD,LM,HH,SBUS
            1,1,sun,0.79679,0.495819,0.324035,0.0
            1,2,mon,0.948027,0.91867,0.893196,0.0
        """
        surrs = {}
        f = open(file_path, 'r')
        labels = f.readline().rstrip().split(',')[3:]
        for line in f.xreadlines():
            # read line
            ln = line.rstrip().split(',')
            region = int(ln[0])
            dow = ln[2]
            values = [np.float32(val) for val in ln[3:]]

            # load data into surrogate
            if region not in surrs:
                surrs[region] = {}
            surrs[region][dow] = dict((labels[i], val) for i, val in enumerate(values))

        f.close()
        return surrs
