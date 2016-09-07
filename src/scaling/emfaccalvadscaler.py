
from src.scaling.emfac2014scaler import Emfac2014Scaler
from src.emissions.sparce_emissions import SparceEmissions


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

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region, dow=2, hr=0):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatial_surrs[veh][act] = SpatialSurrogate()
                                      SpatialSurrogate[(grid, cell)] = fraction
            output: {EIC: SparceEmissions[(grid, cell)][pollutant] = value}
        """
        e = {}

        # loop through each on-road EIC
        for eic in emis_table:
            se = SparceEmissions()
            veh, act = self.eic2dtim4[eic]

            # fix VMT activity according to CSTDM periods
            if act[:3] in ['vmt', 'vht']:
                act += self.DOWS[dow] + self.CALVAD_HOURS[hr]

            # add emissions to sparce grid
            for poll, value in emis_table[eic].iteritems():
                if act not in spatial_surrs[veh]:
                    continue
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se[cell][poll] = value * fraction

            # add NH3, based on CO fractions
            nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, 0.0)
            if 'co' in emis_table[eic] and nh3_fraction:
                value = emis_table[eic]['co']
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se[cell]['nh3'] = value * fraction * nh3_fraction

            e[eic] = se

        return e
