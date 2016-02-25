
from version import __version__


class EstaModel(object):

    def __init__(self, spatial_loaders, temporal_loaders, emis_loaders, emis_scaler, writers, tests):
        self.spatial_loaders = spatial_loaders
        self.temporal_loaders = temporal_loaders
        self.emis_loaders = emis_loaders
        self.emis_scaler = emis_scaler
        self.writers = writers
        self.testers = tests
        self.spatial_surrs = None
        self.temporal_surrs = None
        self.emissions = None
        self.scaled_emissions = None

    def process(self):
        ''' build the spatial and temporal surrogates and apply them to
            the emissions
        '''
        print('\nExecuting ESTA model v' + __version__)
        # reset all data
        self.spatial_surrs = None
        self.temporal_surrs = None
        self.emissions = None
        self.scaled_emissions = None

        print('  - loading spatial surrogates')
        for spatial_loader in self.spatial_loaders:
            self.spatial_surrs, self.temporal_surrs = spatial_loader.load(self.spatial_surrs,
                                                                          self.temporal_surrs)

        print('  - loading temporal surrogates')
        for temporal_loader in self.temporal_loaders:
            self.temporal_surrs = temporal_loader.load(self.spatial_surrs, self.temporal_surrs)

        print('  - loading emissions data')
        for emis_loader in self.emis_loaders:
            self.emissions = emis_loader.load(self.emissions)

        print('  - scaling emissions')
        self.scaled_emissions = self.emis_scaler.scale(self.emissions, self.spatial_surrs,
                                                       self.temporal_surrs)

        print('  - writing output files')
        for writer in self.writers:
            writer.write(self.scaled_emissions)

    def postprocess(self):
        ''' run all listed tests '''
        print('  - testing output files')
        for tester in self.testers:
            tester.test()
