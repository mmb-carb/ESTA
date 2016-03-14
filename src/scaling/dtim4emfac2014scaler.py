
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
from pandas.tseries.holiday import USFederalHolidayCalendar
from src.core.emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from src.core.eic_utils import eic_reduce
from src.emissions.sparce_emissions import SparceEmissions


class Dtim4Emfac2014Scaler(EmissionsScaler):

    CALVAD_TYPE = [1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1,
                   1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1]
    DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}

    def __init__(self, config):
        super(Dtim4Emfac2014Scaler, self).__init__(config)
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.eic2dtim4 = eval(open(self.config['Scaling']['eic2dtim4'], 'r').read())
        self.nh3_fractions = {}

    def scale_OLD(self, emissions, spatial_surr, temporal_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
            INPUT FORMATS:
            Emissions: EMFAC2014EmissionsData
                            emis_data[county][date string] = EmissionsTable
                            EmissionsTable[EIC][pollutant] = value
            Spatial Surrogates: Dtim4SpatialData
                                    data[county][date][hr][veh][act] = SpatialSurrogate()
                                    SpatialSurrogate[(grid, cell)] = fraction
            Temporal Surrogates: {'diurnal': Dtim4TemporalData(),
                                  'dow': calvad[county][dow][ld/lm/hh] = fraction}
                                  Dtim4TemporalData
                                        data[county][date][veh][act] = TemporalSurrogate()
                                            TemporalSurrogate = [x]*24
            OUTPUT FORMAT:
            ScaledEmissions: data[county][date][hr][eic] = SparceEmissions
                                SparceEmissions[(grid, cell)][pollutant] = value
        """
        self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])
        e = ScaledEmissions()

        # loop through all the county/date combinations in the emissions
        for county in self.subareas:
            county_data = emissions.data[county]
            for date, et in county_data.iteritems():
                # find the DOW
                if date[4:] in self._find_holidays():
                    dow = 'holi'
                else:
                    by_date = str(self.base_year) + date[4:]
                    dow = Dtim4Emfac2014Scaler.DOW[dt.strptime(by_date, self.date_format).weekday()]

                # apply CalVad DOW factors
                cal_factors = temporal_surr['dow'][county][dow]
                emissions_table = deepcopy(et)
                emissions_table = self._apply_factors(emissions_table, cal_factors)

                # find diurnal factors by hour
                factors_by_hour = temporal_surr['diurnal'][county][dow]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[county][date]

                # loop through each hour of the day
                for hr in xrange(24):
                    # apply diurnal profile to emissions
                    emis_table = deepcopy(emissions_table)
                    emis_table = self._apply_factors(emis_table, factors_by_hour[hr])

                    # apply spatial surrogates & create sparcely-gridded emissions
                    sparce_emis_dict = self._apply_spatial_surrs(county, emis_table, spatial_surrs)

                    for eic, sparce_emis in sparce_emis_dict.iteritems():
                        eic1 = self.eic_reduce(eic)
                        e.set(county, date, hr + 1, eic1, sparce_emis)

        return e

    def scale(self, emissions, spatial_surr, temporal_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
            INPUT FORMATS:
            Emissions: EMFAC2014EmissionsData
                            emis_data[county][date string] = EmissionsTable
                            EmissionsTable[EIC][pollutant] = value
            Spatial Surrogates: Dtim4SpatialData
                                    data[county][date][hr][veh][act] = SpatialSurrogate()
                                    SpatialSurrogate[(grid, cell)] = fraction
            Temporal Surrogates: {'diurnal': Dtim4TemporalData(),
                                  'dow': calvad[county][dow][ld/lm/hh] = fraction}
                                  Dtim4TemporalData
                                        data[county][date][veh][act] = TemporalSurrogate()
                                            TemporalSurrogate = [x]*24
            OUTPUT FORMAT:
            ScaledEmissions: data[county][date][hr][eic] = SparceEmissions
                                SparceEmissions[(grid, cell)][pollutant] = value
            NOTE: This function is a generator and will `yield` emissions on a file-by-file
                  basis, rather than `return` them.
        """
        self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])

        # loop through all the dates in the period
        today = dt(self.start_date.year, self.start_date.month, self.start_date.day)
        while today <= self.end_date:
            e = ScaledEmissions()
            date = today.strftime(self.date_format)
            # find the DOW
            if date[4:] in self._find_holidays():
                dow = 'holi'
            else:
                by_date = str(self.base_year) + date[4:]
                dow = Dtim4Emfac2014Scaler.DOW[dt.strptime(by_date, self.date_format).weekday()]

            for county in self.subareas:
                if date not in emissions.data[county]:
                    continue
                et = emissions.data[county][date]

                # apply CalVad DOW factors
                cal_factors = temporal_surr['dow'][county][dow]
                emissions_table = deepcopy(et)
                emissions_table = self._apply_factors(emissions_table, cal_factors)

                # find diurnal factors by hour
                factors_by_hour = temporal_surr['diurnal'][county][dow]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[county][date]

                # loop through each hour of the day
                for hr in xrange(24):
                    # apply diurnal profile to emissions
                    emis_table = deepcopy(emissions_table)
                    emis_table = self._apply_factors(emis_table, factors_by_hour[hr])

                    # apply spatial surrogates & create sparcely-gridded emissions
                    sparce_emis_dict = self._apply_spatial_surrs(county, emis_table, spatial_surrs)

                    for eic, sparce_emis in sparce_emis_dict.iteritems():
                        eic1 = self.eic_reduce(eic)
                        e.set(county, date, hr + 1, eic1, sparce_emis)

            yield e
            today += timedelta(days=1)

    def _read_nh3_inventory(self, inv_file):
        """ read the NH3/CO values from the inventory and generate the NH3/CO fractions
            File format:
            fyear,co,ab,dis,facid,dev,proid,scc,sic,eic,pol,ems
            2012,33,SC,SC,17953,1,11,39000602,3251,5007001100000,42101,5.418156170044^M
        """
        inv = {}
        f = open(inv_file, 'r')
        header = f.readline()

        for line in f.xreadlines():
            # parse line
            ln = line.strip().split(',')
            poll = int(ln[-2])
            if poll not in [42101, 7664417]:
                continue
            county = int(ln[1])
            eic = int(ln[-3])
            val = float(ln[-1])

            # fill data structure
            if county not in inv:
                inv[county] = defaultdict(float)
            if eic not in inv[county]:
                inv[county][eic] = {42101: 0.0, 7664417: 0.0}
            # fill in emissions values
            inv[county][eic][poll] += val
        f.close()

        # create fractions
        for county in inv:
            for eic in inv[county]:
                co = inv[county][eic][42101]
                if co == 0.0:
                    inv[county][eic] = 0.0
                else:
                    nh3 = inv[county][eic][7664417]
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

    def _apply_spatial_surrs(self, county, emis_table, spatial_surrs):
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
                    if poll == 'co':
                        # TODO: remove this `if` and add a single comprehension outside this loop?
                        # TODO: That would mean flipping cell and poll in this dictionary
                        se[cell]['nh3'] = se[cell]['co'] * self.nh3_fractions[county][eic]
            e[eic] = se

        return e

    def _find_holidays(self):
        '''Using Pandas calendar, find all 10 US Federal Holidays,
        plus California's Cesar Chavez day'''
        yr = str(self.base_year)
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()

        return [d.strftime('%m-%d') for d in holidays] + ['03-31']
