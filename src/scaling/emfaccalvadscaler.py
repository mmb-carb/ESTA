
import numpy as np
from src.scaling.emfac2014scaler import Emfac2014Scaler
from src.emissions.sparse_emissions import SparseEmissions


class EmfacCalvadScaler(Emfac2014Scaler):

    ''' Temporal periods defined in CSTDM
        AM Peak   6 AM  to 10 AM
        Midday    10 AM to 3 PM
        PM Peak   3 PM  to 7 PM
        Off-Peak  7 PM  to 6 AM
    '''
    CALVAD_HOURS = ['off', 'off', 'off', 'off', 'off', 'off',
                    'am',  'am',  'am',  'am',  'mid', 'mid',
                    'mid', 'mid', 'mid', 'pm',  'pm',  'pm',
                    'pm',  'off', 'off', 'off', 'off', 'off']
    DOWS = ['_monday_', '_tuesday_', '_wednesday_', '_thursday_', '_friday_',
            '_saturday_', '_sunday_', '_holiday_']

    def __init__(self, config, position):
        super(EmfacCalvadScaler, self).__init__(config, position)
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region, dow=2, hr=0):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatial_surrs[veh][act] = SpatialSurrogate()
                                      SpatialSurrogate[(grid, cell)] = fraction
            output: {EIC: SparseEmissions[pollutant][(grid, cell)] = value}
        """
        e = {}

        # loop through each on-road EIC
        for eic in emis_table:
            se = SparseEmissions(self.nrows, self.ncols)
            veh, act = self.eic2dtim4[eic]

            # fix VMT activity according to CSTDM periods
            if act[:3] in ['vmt', 'vht']:
                act += self.DOWS[dow] + self.CALVAD_HOURS[hr]

            # add emissions to sparse grid
            for poll, value in emis_table[eic].iteritems():
                if act not in spatial_surrs[veh]:
                    continue
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se.add(poll, cell, value * fraction)

            # add NH3, based on CO fractions
            nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, np.float32(0.0))
            if 'co' in emis_table[eic] and nh3_fraction:
                value = emis_table[eic]['co']
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se.add('nh3', cell, value * fraction * nh3_fraction)

            e[eic] = se

        return e
