
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
from pandas.tseries.holiday import USFederalHolidayCalendar
from src.core.emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from src.core.eic_utils import eic_reduce
from src.emissions.sparce_emissions import SparceEmissions


class Emfac2014Scaler(EmissionsScaler):

    CALVAD_TYPE = [1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1,
                   1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1]
    DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}

    def __init__(self, config):
        super(Emfac2014Scaler, self).__init__(config)
        by_region = self.config['Output']['by_region'].lower()
        self.by_region = False if by_region in ['false', '0', 'no'] else True
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.eic2dtim4 = eval(open(self.config['Scaling']['eic2dtim4'], 'r').read())
        self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])

    def scale(self, emissions, spatial_surr, temp_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
            INPUT FORMATS:
            Emissions: EMFAC2014EmissionsData
                            emis_data[region][date string] = EmissionsTable
                            EmissionsTable[EIC][pollutant] = value
            Spatial Surrogates: Dtim4SpatialData
                                    data[region][date][hr][veh][act] = SpatialSurrogate()
                                    SpatialSurrogate[(grid, cell)] = fraction
            Temporal Surrogates: {'diurnal': Dtim4TemporalData(),
                                  'dow': calvad[region][dow][ld/lm/hh] = fraction}
                                  Dtim4TemporalData
                                        data[region][date][veh][act] = TemporalSurrogate()
                                            TemporalSurrogate = [x]*24
            OUTPUT FORMAT:
            ScaledEmissions: data[region][date][hr][eic] = SparceEmissions
                                SparceEmissions[(grid, cell)][pollutant] = value
            NOTE: This function is a generator and will `yield` emissions file-by-file.
        """
        today = dt(self.start_date.year, self.start_date.month, self.start_date.day)

        # loop through all the dates in the period
        while today <= self.end_date:
            # find the DOW
            date = today.strftime(self.date_format)
            today += timedelta(days=1)
            if date[4:] in self._find_holidays():
                dow = 'holi'
            else:
                by_date = str(self.base_year) + date[4:]
                dow = Emfac2014Scaler.DOW[dt.strptime(by_date, self.date_format).weekday()]

            # if not by sub-region, create emissions object
            if not self.by_region:
                e = ScaledEmissions()

            for region in self.regions:
                if date not in emissions.data[region]:
                    continue

                # if by sub-area, create emissions object
                if self.by_region:
                    e = ScaledEmissions()

                # apply CalVad DOW factors (this line is long for performance reasons)
                emissions_table = self._apply_factors(deepcopy(emissions.data[region][date]),
                                                      temp_surr['dow'][region][dow])

                # find diurnal factors by hour
                factors_by_hour = temp_surr['diurnal'][region][dow]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[region]

                # loop through each hour of the day
                for hr in xrange(24):
                    # apply diurnal, then spatial profiles (this line long for performance reasons)
                    sparce_emis_dict = self._apply_spatial_surrs(self._apply_factors(deepcopy(emissions_table),
                                                                                     factors_by_hour[hr]),
                                                                 spatial_surrs, region)

                    for eic, sparce_emis in sparce_emis_dict.iteritems():
                        e.set(region, date, hr + 1, self.eic_reduce(eic), sparce_emis)

                # yield, if by sub-area
                if self.by_region:
                    yield e

            # yield, if not by sub-area
            if not self.by_region:
                yield e

    def _read_nh3_inventory(self, inv_file):
        """ read the NH3/CO values from the inventory and generate the NH3/CO fractions
            File format:
            fyear,co,ab,dis,facid,dev,proid,scc,sic,eic,pol,ems
            2012,33,SC,SC,17953,1,11,39000602,3251,5007001100000,42101,5.418156170044^M
        """
        co_id = 42101
        nh3_id = 7664417
        inv = {}
        f = open(inv_file, 'r')
        header = f.readline()

        for line in f.xreadlines():
            # parse line
            ln = line.strip().split(',')
            poll = int(ln[-2])
            if poll not in [co_id, nh3_id]:
                continue
            county = int(ln[1])
            eic = int(ln[-3])
            val = float(ln[-1])

            # fill data structure
            if county not in inv:
                inv[county] = defaultdict(float)
            if eic not in inv[county]:
                inv[county][eic] = {co_id: 0.0, nh3_id: 0.0}
            # fill in emissions values
            inv[county][eic][poll] += val
        f.close()

        # create fractions
        for county in inv:
            for eic in inv[county]:
                co = inv[county][eic][co_id]
                if co == 0.0:
                    inv[county][eic] = 0.0
                else:
                    nh3 = inv[county][eic][nh3_id]
                    inv[county][eic] = nh3 / co

        return inv

    def _apply_factors(self, emissions_table, factors):
        """ Apply CalVad DOW or diurnal factors to an emissions table, altering the table.
            Date Types:
            EmissionsTable[EIC][pollutant] = value
            factors = [ld, lm, hh, sbus]
        """
        for eic in emissions_table:
            factor = factors[self.CALVAD_TYPE[self.eic2dtim4[eic][0]]]
            emissions_table[eic].update((x, y * factor) for x, y in emissions_table[eic].items())

        return emissions_table

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatil_surrs[veh][act] = SpatialSurrogate()
                                    SpatialSurrogate[(grid, cell)] = fraction
            output: {EIC: SparceEmissions[(grid, cell)][pollutant] = value}
        """
        e = {}
        for eic in emis_table:
            se = SparceEmissions()
            veh, act = self.eic2dtim4[eic]
            for poll, value in emis_table[eic].iteritems():
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se[cell][poll] = value * fraction

            # Add NH3, based on CO fractions
            nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, 0.0)
            if 'co' in emis_table[eic] and nh3_fraction:
                value = emis_table[eic]['co']
                for cell, fraction in spatial_surrs[veh][act].iteritems():
                    se[cell]['nh3'] = value * fraction * nh3_fraction

            e[eic] = se

        return e

    def _find_holidays(self):
        ''' Using Pandas calendar, find all 10 US Federal Holidays,
            plus California's Cesar Chavez Day (March 31).
        '''
        yr = str(self.base_year)
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()

        return [d.strftime('%m-%d') for d in holidays] + ['03-31']
