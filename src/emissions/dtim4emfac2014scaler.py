
from eic2dtim4 import eic2dtim4
from emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from sparce_emissions import SparceEmissions


class Dtim4Emfac2014Scaler(EmissionsScaler):

    def __init__(self, config):
        super(Dtim4Emfac2014Scaler, self).__init__(config)
        self.date_format = self.config['Dates']['format']
        self.start_date = datetime.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = datetime.strptime(self.config['Dates']['end'], self.date_format)

    def scale(self, emissions, spatial_surr, temporal_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
        """
        e = ScaledEmissions()

        return e
