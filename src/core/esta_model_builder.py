
import os
import sys
from src.core.esta_model import EstaModel


class EstaModelBuilder(object):

    def __init__(self, config_dict):
        self.config = config_dict

    def build(self):
        '''Perform various pre-processing steps, then return an EstaModel object'''
        print('\nBuilding ESTA model chain')
        spatial_loaders, temporal_loaders = self.build_surrogate_loaders()
        emissions_loaders = self.build_emissions_loaders()
        scaler = self.build_emissions_scaler()
        writers = self.build_output_writers()
        testers = self.build_output_testers()

        return EstaModel(spatial_loaders, temporal_loaders, emissions_loaders, scaler, writers,
                         testers)

    def build_surrogate_loaders(self):
        ''' the classes used to load spatial and temporal surrogates '''
        # read config file options
        spatial_directories = self.config['Surrogates']['spatial_directories'].split()
        spatial_loader_strs = self.config['Surrogates']['spatial_loaders'].split()
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
        for i in xrange(len(spatial_loader_strs)):
            sl = spatial_loader_strs[i]
            try:
                __import__('src.surrogates.' + sl.lower())
                mod = sys.modules['src.surrogates.' + sl.lower()]
                spatial_loaders.append(getattr(mod, sl)(self.config, spatial_directories[i]))
            except (NameError, KeyError) as e:
                sys.exit('ERROR: Unable to find class: ' + sl + '\n' + str(e))

        # validate temporal surrogate input directories
        for td in temporal_directories:
            if not os.path.exists(td):
                sys.exit('ERROR: Input directory not found: ' + td)

        # validate that we have the same number of directories as temporal loaders
        if len(temporal_directories) != len(temporal_loader_strs):
            sys.exit('ERROR: Different number of temporal loaders and directories.')

        # build list of temporal surrogate loader objects
        temporal_loaders = []
        for i in xrange(len(temporal_directories)):
            tl = temporal_loader_strs[i]
            try:
                __import__('src.surrogates.' + tl.lower())
                mod = sys.modules['src.surrogates.' + tl.lower()]
                temporal_loaders.append(getattr(mod, tl)(self.config, temporal_directories[i]))
            except (NameError, KeyError) as e:
                sys.exit('ERROR: Unable to find class: ' + tl + '\n' + str(e))

        return spatial_loaders, temporal_loaders

    def build_emissions_loaders(self):
        ''' the classes used to load emissions files '''
        directories = self.config['Emissions']['emissions_directories'].split()
        loader_strs = self.config['Emissions']['emissions_loaders'].split()
        time_units = self.config['Emissions']['time_units'].split()

        # validate that we have the same number of directories, loaders, and time units
        if len(directories) != len(loader_strs) or len(directories) != len(time_units):
            sys.exit('ERROR: Different number of emission loaders, directories, and time units.')

        # build list of emission loader objects
        loaders = []
        for i in xrange(len(loader_strs)):
            el = loader_strs[i]
            try:
                __import__('src.emissions.' + el.lower())
                mod = sys.modules['src.emissions.' + el.lower()]
                loaders.append(getattr(mod, el)(self.config, directories[i], time_units[i]))
            except (NameError, KeyError) as e:
                sys.exit('ERROR: Unable to find class: ' + el + '\n' + str(e))

        return loaders

    def build_emissions_scaler(self):
        ''' Load the single class used to scale emissions into gridded, hourly results '''
        return self._init_basic_class(self.config['Scaling']['scalor'], 'scaling')

    def build_output_writers(self):
        ''' The classes used to load your various emissions files '''
        writer_strs = self.config['Output']['writers'].split()

        # build list of output writer objects
        loaders = []
        for writer_string in writer_strs:
            loaders.append(self._init_basic_class(writer_string, 'output'))

        return loaders

    def build_output_testers(self):
        ''' The classes used to test your various output files '''
        tester_strs = self.config['Testing']['tests'].split()

        # build list of output tester objects
        testers = []
        for tester_string in tester_strs:
            testers.append(self._init_basic_class(tester_string, 'testing'))

        return testers

    def _init_basic_class(self, class_string, step_string):
        ''' Find a class in a given step of the ESTA source code,
            and initialize it.
            (Only works for classes that only take the config object to initialize.)
        '''
        try:
            __import__('src.' + step_string + '.' + class_string.lower())
            mod = sys.modules['src.' + step_string + '.' + class_string.lower()]
            return getattr(mod, class_string)(self.config)
        except (NameError, KeyError) as e:
            sys.exit('ERROR: Unable to find class: ' + class_string + '\n' + str(e))
