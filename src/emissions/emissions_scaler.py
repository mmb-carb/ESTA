
import abc

class EmissionsScaler(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config
        self.new_emissions = None

    @abc.abstractmethod
    def scale(self, emissions, spatial_surr, temporal_surr):
        return None
