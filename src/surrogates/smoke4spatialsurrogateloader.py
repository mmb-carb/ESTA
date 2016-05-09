
import os
from spatial_surrogate import SpatialSurrogate
from src.core.spatial_loader import SpatialLoader
from dtim4loader import SpatialSurrogateData


class Smoke4SpatialSurrogateLoader(SpatialLoader):
    ''' This class takes a simple list of EICs and a SMOKE v4 spatial surrogate file
        and creates an ESTA spatial surrogate.
        The SMOKE spatial surrogate format is well-documented and widely used.
    '''

    def __init__(self, config, directory):
        super(Smoke4SpatialSurrogateLoader, self).__init__(config, directory)
        self.smoke_surrogates = self.config.getlist('Surrogates', 'smoke4_surrogates')
        self.eic_files = self.config.getlist('Surrogates', 'eic_files')
        if len(self.smoke_surrogates) != len(self.eic_files):
            exit('ERROR: You need the same number of SMOKE surrogates as EIC list files.')
        self.eic2dtim4 = self.config.eval_file('Scaling', 'eic2dtim4')
        self.gai_codes = self.config.eval_file('Scaling', 'gai_codes')
        self.has_subregions = self.config.getboolean('Regions', 'has_subregions')

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read an EPA SMOKE v4
            spatial surrogate.
        """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = SpatialSurrogateData()

        # loop through each SMOKE 4 surrogate file, and related list of EICs
        for i,surr_file_path in enumerate(self.smoke_surrogates):
            # read list of EICs from file
            eic_path = os.path.join(self.directory, self.eic_files[i])
            eics = Smoke4SpatialSurrogateLoader.load_eics(eic_path)

            # create list of veh/act pairs
            veh_act_pairs = [self.eic2dtim4[eic] for eic in eics]

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
            County-based File format:           GAI-based File format:
            #GRID... header info                #GRID... header info
            105;06030;238;44;0.00361888         440;0SC006030;237;45;0.00052883
            105;06030;237;45;0.00476944         440;0SC006030;238;45;0.00443297
        '''
        surrogates = {}
        f = open(file_path, 'r')
        header = f.readline()
        for line in f.xreadlines():
            ln = line.rstrip().split(';')
            if len(ln) != 5:
                continue
            if self.has_subregions:
                region = int(ln[1][2:])
            else:
                region = self.gai_codes[ln[1]]
            y = int(ln[2])
            x = int(ln[3])
            fraction = float(ln[4])

            if region not in surrogates:
                surrogates[region] = SpatialSurrogate()
            surrogates[region][(x, y)] = fraction

        f.close()
        return surrogates

    @staticmethod
    def load_eics(file_path):
        ''' Load a simple text file: just a list of EICs that will use the
            new SMOKE v4 spatial surrogate.
            File Format:
            71070111000000
            74676854107026
        '''
        text = open(file_path, 'r').read()
        return [int(eic) for eic in text.split()]
