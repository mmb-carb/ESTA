
import os
import sys
from src.esta.esta_model import EstaModel


class EstaModelBuilder(object):

    def __init__(self, config_dict):
        self.config = config_dict

    def build(self):
        '''Perform various pre-processing steps, then return an EstaModel object'''
        print('\nBuilding ESTA model chain')
        spatial_loaders, temporal_loaders = self.build_surrogate_loaders()
        #emissions_loader = self.build_emissions_loaders()
        #output_writers = self.build_output_writers()

        #return EstaModel(surr_loaders,, temporal_loaders emis_loaders, output_writers, grid,
        #                  sub_areas, dates, in_dir)
        return EstaModel(spatial_loaders, temporal_loaders, None, None, None, None, None, None)

    def build_surrogate_loaders(self):
        ''' The spatial and temporal surrogates are built from '''
        # read config file options
        spatial_directories = self.config['Surrogates']['spatial_directories'].split()
        spatial_loader_strs = self.config['Surrogates']['spatial_loaders'].split()
        temporal_separate = self.config['Surrogates']['temporal_separate']
        temporal_directories = self.config['Surrogates']['temporal_directories'].split()
        temporal_loader_strs = self.config['Surrogates']['temporal_loaders'].split()

        # validate spatial surrogate input directories
        for sd in spatial_directories:
            if not os.path.exists(sd):
                sys.exit('ERROR: Input directory not found: ' + sd)

        # validate that we have the same number of directories as spatial loaders
        if len(spatial_directories) != len(spatial_loader_strs):
            sys.exit('ERROR: Different number of spatial loaders and directories.')

        # build list of spatial surrogate loader objects
        spatial_loaders = []
        for i in xrange(len(i)):
            sl = spatial_loader_strs[i]
            try:
                mod = sys.modules[sl.lower()]
                spatial_loaders.append(getattr(mod, sl)(spatial_directories[i]))
            except NameError as ne:
                sys.exit('ERROR: Unable to find class: ' + sl + '\n' + ne)

        # If we are using the same classes to load spatial and temporal surrogates, we're done.
        if temporal_separate.lower() in ['false', 'no', '0', 'na', 'none']:
            return spatial_loaders, []

        # validate temporal surrogate input directories
        for td in temporal_directories:
            if not os.path.exists(td):
                sys.exit('ERROR: Input directory not found: ' + td)

        # validate that we have the same number of directories as temporal loaders
        if len(temporal_directories) != len(temporal_loader_strs):
            sys.exit('ERROR: Different number of temporal loaders and directories.')

        # build list of temporal surrogate loader objects
        temporal_loaders = []
        for i in xrange(len(i)):
            tl = spatial_loader_strs[i]
            try:
                mod = sys.modules[tl.lower()]
                temporal_loaders.append(getattr(mod, tl)(temporal_directories[i]))
            except NameError as ne:
                sys.exit('ERROR: Unable to find class: ' + tl + '\n' + ne)

        return spatial_loaders, temporal_loaders
