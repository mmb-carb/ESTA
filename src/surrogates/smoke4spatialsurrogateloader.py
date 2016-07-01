
import os
import sys
from spatial_surrogate import SpatialSurrogate
from src.core.spatial_loader import SpatialLoader
from dtim4loader import SpatialSurrogateData


class Smoke4SpatialSurrogateLoader(SpatialLoader):
    ''' This class takes a simple list of EICs and a SMOKE v4 spatial surrogate file
        and creates an ESTA spatial surrogate.
        The SMOKE spatial surrogate format is well-documented and widely used.
    '''

    def __init__(self, config, position):
        super(Smoke4SpatialSurrogateLoader, self).__init__(config, position)
        self.eic2dtim4 = self.config.eval_file('Surrogates', 'eic2dtim4')
        self.smoke_surrogates = self.config.getlist('Surrogates', 'smoke4_surrogates')
        self.eic_labels = self.config.getlist('Surrogates', 'smoke_eic_labels')
        if len(self.smoke_surrogates) != len(self.eic_labels):
            sys.exit('ERROR: You need the same number of SMOKE surrogates as EIC labels.')
        self.gai_codes = self.config.eval_file('Scaling', 'gai_codes')

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read an EPA SMOKE v4
            spatial surrogate.
        """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = SpatialSurrogateData()

        # loop through each SMOKE 4 surrogate file, and related list of EICs
        for i,surr_file_path in enumerate(self.smoke_surrogates):
            # create list of veh/act pairs
            veh_act_pairs = self._create_veh_act_pairs(i)

            # read SMOKE v4 spatial surrogate
            surrogate_file_path = os.path.join(self.directory, surr_file_path)
            surrogates = self._load_surrogates(surrogate_file_path)

            # set the spatial surrogate above for each and every veh/act pair
            for veh,act in veh_act_pairs:
                for region, surrogate in surrogates.iteritems():
                    spatial_surrogates.set(region, veh, act, surrogate)

        # normalize surrogates
        spatial_surrogates.surrogates()

        return spatial_surrogates, temporal_surrogates

    def _load_surrogates(self, file_path):
        ''' Load a SMOKE v4 spatial surrogate text file.
            Use it to create an ESTA spatial surrogate.
            GAI-based File format:
            #GRID... header info
            440;0SC006030;237;45;0.00052883
            440;0SC006030;238;45;0.00443297
        '''
        surrogates = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            ln = line.rstrip().split(';')
            if len(ln) != 5:
                continue
            region = self.gai_codes[ln[1]]
            y = int(ln[2])
            x = int(ln[3])
            fraction = float(ln[4])

            if region not in surrogates:
                surrogates[region] = SpatialSurrogate()
            surrogates[region][(x, y)] = fraction

        f.close()
        return surrogates

    def _create_veh_act_pairs(self, i):
        ''' create list of veh/act pairs for a given set of EICs '''
        # read list of EICs from file
        label = self.eic_labels[i]

        eics = sorted([eic for eic in self.eic2dtim4 if self.eic2dtim4[eic][1] == label])
        veh_act_pairs = [self.eic2dtim4[eic] for eic in eics]

        return veh_act_pairs
