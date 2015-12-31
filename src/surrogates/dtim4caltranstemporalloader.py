
from temporal_loader import TemporalLoader


class Dtim4CaltransTemporalLoader(TemporalLoader):

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    def load(self, spatial_surrogates, temporal_surrogates):
        return
