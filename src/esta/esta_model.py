

class EstaModel(object):

    def __init__(self, spatial_loaders, temporal_loaders, emis_loaders, output_writer, grid,
                 sub_areas, dates, in_dir):
        self.spatial_loaders = spatial_loaders
        self.temporal_loaders = temporal_loaders
        self.emis_loaders = emis_loaders
        self.output_writers = output_writers
        self.grid = grid
        self.sub_areas = sub_areas
        self.dates = dates
        self.in_dir = in_dir
        self.spatial_surr = None
        self.temporal_surr = None
        self.emissions = None
        self.gridded_emissions = None

    def process(self):
        ''' build the spatial and temporal surrogates and apply them to
            the emissions
        '''
        # load all spatial data
        self.spatial_surr = None
        for spatial_loader in self.spatial_loaders:
            spatial_loader.load(self.spatial_surr)

        # load all temporal data
        self.temporal_surr = None
        for temporal_loader in self.temporal_loaders:
            temporal_loader.load(self.temporal_surr)

        # load all emissions data
        self.emissions = None
        for emis_loader in self.emis_loaders:
            emis_loader.load(self.emissions)

        self.load_spatial_surrogates()
        self.load_temporal_surrogates()
        self.surrogates = self.surrogate_gen.generate()
        self.daily_emis = self.emissions_gen.generate()
        self.temporal_profs = self.temporal_prof_gen.generate()
        self.speciation_refs, self.speciation_profs = self.speciation_profs_gen.generate()

    def gen_output_files(self):
        ''' Put the new gridded, temporal emissions data into the final, formatted
            output files.
        '''
        self.output_writer(self.gridded_emissions)

