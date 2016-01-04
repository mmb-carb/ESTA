

class EstaModel(object):

    def __init__(self, spatial_loaders, temporal_loaders, emis_loaders, emis_scaler,
                 subarea_writers, general_writers, grid, sub_areas, dates, in_dir):
        self.spatial_loaders = spatial_loaders
        self.temporal_loaders = temporal_loaders
        self.emis_loaders = emis_loaders
        self.emis_scaler = emis_scaler
        self.subarea_writers = subarea_writers
        self.general_writers = general_writers
        self.grid = grid
        self.sub_areas = sub_areas
        self.dates = dates
        self.in_dir = in_dir
        self.spatial_surrs = None
        self.temporal_surrs = None
        self.emissions = None
        self.scaled_emissions = None

    def process(self):
        ''' build the spatial and temporal surrogates and apply them to
            the emissions
        '''
        # reset all data
        self.spatial_surrs = None
        self.temporal_surrs = None
        self.emissions = None
        self.scaled_emissions = None
        
        # load all spatial data
        for spatial_loader in self.spatial_loaders:
            self.spatial_surrs, self.temporal_surrs = spatial_loader.load(self.spatial_surrs,
                                                                          self.temporal_surrs)

        # load all temporal data
        for temporal_loader in self.temporal_loaders:
            self.temporal_surrs = temporal_loader.load(self.spatial_surrs, self.temporal_surrs)

        # load all emissions data
        for emis_loader in self.emis_loaders:
            self.emissions = emis_loader.load(self.emissions)

        # scaling the emissions, based on the above surrogates
        self.scaled_emissions = self.emis_scaler.scale(self.emissions, self.spatial_surrs,
                                                       self.temporal_surrs)

        # apply surrogates and write output files
        for sub_area in self.sub_areas:
            for subarea_writer in self.subarea_writers:
                subarea_writer.write(self.gridded_emissions, subarea)

        for general_writer in self.general_writers:
                general_writer.write(self.gridded_emissions)

    def gen_output_files(self):
        ''' Put the new gridded, temporal emissions data into the final, formatted
            output files.
        '''
        self.output_writer(self.gridded_emissions)
