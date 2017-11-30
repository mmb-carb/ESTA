
import numpy as np
import os
import sys
from spatial_surrogate import SpatialSurrogate
from src.core.spatial_loader import SpatialLoader
from spatial_surrogate_data import SpatialSurrogateData


class CalvadSmoke4SpatialSurrogateLoader(SpatialLoader):
    ''' This class takes a simple list of EICs and a SMOKE v4 spatial surrogate file
        and creates an ESTA spatial surrogate.
        The SMOKE spatial surrogate format is well-documented and widely used.
        These SMOKE surrogates have a naming convention to allow us to use the four
        daily periods defined by Calvad.
    '''

    PERIODS = ['am', 'mid', 'pm', 'off']

    def __init__(self, config, position):
        super(CalvadSmoke4SpatialSurrogateLoader, self).__init__(config, position)
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        self.smoke_surrogates = self.config.getlist('Surrogates', 'smoke4_surrogates')
        self.eic_labels = self.config.getlist('Surrogates', 'smoke_eic_labels')
        if len(self.smoke_surrogates) != len(self.eic_labels):
            sys.exit('ERROR: You need the same number of SMOKE surrogates as EIC labels.')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.regions = self.config.parse_regions('Regions', 'regions')

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read an EPA SMOKE v4
            spatial surrogate.
        """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = SpatialSurrogateData()
        spatial_surrogates.init_regions(self.regions)

        # loop through each SMOKE surrogate file, and related list of EICs
        for i, surr_file_path in enumerate(self.smoke_surrogates):
            # read SMOKE spatial surrogate
            file_path = os.path.join(self.directory, surr_file_path)
            region_surrogates = self._load_surrogate_file(file_path)

            # create list of veh/act pairs
            veh_act_pairs = self._create_veh_act_pairs(i)

            # set the spatial surrogate above for each and every veh/act pair
            for veh, act in veh_act_pairs:
                for region, surrogate in region_surrogates.iteritems():
                    spatial_surrogates.set_nocheck(region, veh, act, surrogate)

        # normalize surrogates
        spatial_surrogates.surrogates()

        return spatial_surrogates, temporal_surrogates

    def _load_surrogate_file(self, file_path):
        ''' Load a SMOKE v4 spatial surrogate text file.
            Use it to create an ESTA spatial surrogate.
            GAI-based File format:
            #GRID... header info
            440;06030;237;45;0.00052883
            440;06030;238;45;0.00443297
        '''
        # create a dict of surrogates for each region in this file
        surrogates = {}
        for region in self.regions:
            surrogates[region] = SpatialSurrogate()

        # process multi-region surrogate file
        f = open(file_path, 'r')
        _ = f.readline()
        for line in f.xreadlines():
            ln = line.rstrip().split(';')
            if len(ln) != 5:
                continue
            region = int(ln[1]) % 1000
            if region not in self.regions:
                continue

            # re-wrote for speed
            #cell = (int(ln[3]) - 1, int(ln[2]) - 1)  # (x, y)
            #fraction = np.float32(ln[4])
            surrogates[region][(int(ln[3]) - 1, int(ln[2]) - 1)] = np.float32(ln[4])

        f.close()
        return surrogates

    def _create_veh_act_pairs(self, i):
        ''' create list of veh/act pairs for a given set of EICs '''
        # read list of EICs from config.ini file
        label = self.eic_labels[i]
        period = label.split('_')[-1]
        if period not in ['am', 'mid', 'pm', 'off']:
            period = ''

        # select all EICs whose label in the config.ini file matches a label in the eic_info.py file
        if period:
            short_label = label[:-1 - len(period)]
            eics = [eic for eic in self.eic_info if self.eic_info[eic][1] == short_label]
        else:
            eics = [eic for eic in self.eic_info if self.eic_info[eic][1] == label]

        # collect all vehicle / activity pairs that are relevant to this surrogate
        if period:
            veh_act_pairs = []
            for eic in eics:
                veh, act = self.eic_info[eic][:2]
                for per in self.PERIODS:
                    veh_act_pairs.append((veh, act + '_' + per))
        else:
            veh_act_pairs = [self.eic_info[eic][:2] for eic in eics]

        return veh_act_pairs
