
from emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from sparce_emissions import SparceEmissions


class Dtim4Emfac2014Scaler(EmissionsScaler):

    def __init__(self, config):
        super(Dtim4Emfac2014Scaler, self).__init__(config)

    def scale(self, emissions, spatial_surr, temporal_surr):
        e = ScaledEmissions()

        return e
