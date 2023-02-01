
from src.core.output_files import OutputFiles
from src.core.version import __version__
import pdb


class EstaModel(object):

    def __init__(self, spatial_loaders, temporal_loaders, emis_loaders, emis_scalars, writers, tests):
        self.spatial_loaders = spatial_loaders
        self.temporal_loaders = temporal_loaders
        self.emis_loaders = emis_loaders
        self.emis_scalars = emis_scalars
        self.writers = writers
        self.testers = tests
        self.spat_surrs = None
        self.temp_surrs = None
        self.emissions = None

    def run(self):
        ''' build the spatial and temporal surrogates and apply them to the emissions,
            create output files, and run any tests
        '''
        print('\nExecuting ESTA model v' + __version__)
        # reset all data
        self.spat_surrs = None
        self.temp_surrs = None
        self.emissions = None

        print('  - loading spatial surrogates')
        for spatial_loader in self.spatial_loaders:
            self.spat_surrs, self.temp_surrs = spatial_loader.load(self.spat_surrs, self.temp_surrs)

        print('  - loading temporal surrogates')
        for temporal_loader in self.temporal_loaders:
            self.temp_surrs = temporal_loader.load(self.spat_surrs, self.temp_surrs)

        print('  - loading emissions data')
        for emis_loader in self.emis_loaders:
            self.emissions = emis_loader.load(self.emissions)

        print('  - scaling emissions & writing files')
        output_files = OutputFiles()
        for scalar in self.emis_scalars:
            for scaled_emissions in scalar.scale(self.emissions, self.spat_surrs, self.temp_surrs):
                for writer in self.writers:
                    output_files.union(writer.write(scaled_emissions))

        if self.testers:
            print('  - testing output files')
        for tester in self.testers:
            tester.test(self.emissions, output_files)

