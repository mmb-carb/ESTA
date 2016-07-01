
import os
import sys
from src.core.esta_model import EstaModel


class EstaModelBuilder(object):

    def __init__(self, config_dict):
        self.config = config_dict

    def build(self):
        '''Perform various pre-processing steps, then return an EstaModel object'''
        print('\nBuilding ESTA model chain')

        spatial_loaders = self._init_classes('Surrogates', 'spatial_loaders')
        temporal_loaders = self._init_classes('Surrogates', 'temporal_loaders')
        emis_loaders = self._init_classes('Emissions', 'emissions_loaders')
        scaler = self._init_classes('Scaling', 'scalor')[0]
        writers = self._init_classes('Output', 'writers')
        testers = self._init_classes('Testing', 'tests')

        return EstaModel(spatial_loaders, temporal_loaders, emis_loaders, scaler, writers, testers)

    def _init_classes(self, section, option):
        ''' Given a list of class names, instantiate a list of primary step
            ESTA classes.
        '''
        class_strings = self.config.getlist(section, option)
        step = section.lower()

        classes = []
        for i, class_string in enumerate(class_strings):
            try:
                __import__('src.' + step + '.' + class_string.lower())
                mod = sys.modules['src.' + step + '.' + class_string.lower()]
                classes.append(getattr(mod, class_string)(self.config, i))
            except (NameError, KeyError) as e:
                sys.exit('ERROR: Unable to find class: ' + class_string + '\n' + str(e))

        return classes
