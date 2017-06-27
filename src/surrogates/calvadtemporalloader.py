
import os
import numpy as np
from src.core.temporal_loader import TemporalLoader

# Calvad vehicle type mapping, used only for DOW temporal profiles
# LDA, LDT1, LDT2, MDV, LHDT1, LHDT2, MHDT, HHDT, OBUS, UBUS, MCY, SBUS, MH
# 0 = LD, 1 = LM, 2 = HH, 3 = SBUS
CALVAD_TYPE = [0, 0, 0, 0, 1, 1, 1, 2, 1, 0, 0, 3, 0,
               0, 0, 0, 0, 1, 1, 1, 2, 1, 0, 0, 3, 0]


class CalvadTemporalLoader(TemporalLoader):

    def __init__(self, config, position):
        super(CalvadTemporalLoader, self).__init__(config, position)
        self.dow_path = os.path.join(self.directory, self.config['Surrogates']['calvad_dow'])
        diurnal_file = self.config['Surrogates']['calvad_diurnal']
        self.diurnal_path = os.path.join(self.directory, diurnal_file)

    def load(self, spatial_surrogates, temporal_surrogates):
        """ master method to load both day-of-week and diurnal CALVAD time profiles """
        if not temporal_surrogates:
            temporal_surrogates = {}

        # load DOW time profiles
        temporal_surrogates['dow'] = CalvadTemporalLoader.load_dow(self.dow_path)

        # load diurnal time profiles
        temporal_surrogates['diurnal'] = CalvadTemporalLoader.load_diurnal(self.diurnal_path)

        return temporal_surrogates

    @staticmethod
    def load_diurnal(file_path):
        """ generate the diurnal temporal surrogates from the CalVad data
            hours range from 0 to 23

            CalVad File Format:
            REGION,DAY,HR,LD,LM,HH,SBUS
            Alameda,sun,00,0.020204,0.040504,0.060651,0.0
            Alameda,sun,01,0.012772,0.038892,0.055813,0.0
        """
        calvad = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            # read line
            ln = line.strip().split(',')
            region = int(ln[0])
            dow = ln[1]
            hr = int(ln[2])
            ld = np.float32(ln[3])
            lm = np.float32(ln[4])
            hh = np.float32(ln[5])
            sbus = np.float32(ln[6])

            # load data into surrogate
            if region not in calvad:
                calvad[region] = {}
            if dow not in calvad[region]:
                calvad[region][dow] = {}
            calvad[region][dow][hr] = [ld, lm, hh, sbus]

        f.close()

        return calvad

    @staticmethod
    def load_dow(file_path):
        """ generate the DOW temporal surrogates from the CalVad data

            CalVad File Format:
            REGION,Day,DOW,LD,LM,HH,SBUS
            1,1,sun,0.79679,0.495819,0.324035,0.0
            1,2,mon,0.948027,0.91867,0.893196,0.0
            1,3,tuth,1,1,1
        """
        calvad = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            # read line
            ln = line.strip().split(',')
            region = int(ln[0])
            dow = ln[2]
            ld = np.float32(ln[3])
            lm = np.float32(ln[4])
            hh = np.float32(ln[5])
            sbus = np.float32(ln[6])

            # load data into surrogate
            if region not in calvad:
                calvad[region] = {}
            calvad[region][dow] = [ld, lm, hh, sbus]

        f.close()

        return calvad
