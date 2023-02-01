
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
from scaled_emissions import ScaledEmissions
from src.core.date_utils import DOW, find_holidays
from src.core.emissions_scaler import EmissionsScaler
from src.core.eic_utils import eic_reduce
from src.emissions.sparse_emissions import SparseEmissions
import pdb


class EmfacSmokeScaler(EmissionsScaler):

    PERIODS_BY_HR = ['OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF',  # off peak: 6 AM to 10 AM
                     'AM',  'AM',  'AM',  'AM',  'MID', 'MID',  # midday:   10 AM to 3 PM
                     'MID', 'MID', 'MID', 'PM',  'PM',  'PM',   # pm peak:  3 PM to 7 PM
                     'PM',  'OFF', 'OFF', 'OFF', 'OFF', 'OFF']  # off peak: 7 PM to 6 AM

    def __init__(self, config, position):
        super(EmfacSmokeScaler, self).__init__(config, position)
        self.by_region = 'CmaqNetcdfWriter' not in self.config.getlist('Output', 'writers')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.reverse_regions = dict(((d['air_basin'], d['county'], d['district']), g) for g,d in self.region_info.iteritems())
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        #self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.is_smoke4 = 'smoke4' in self.config['Surrogates']['spatial_loaders'].lower()

    def scale(self, emissions, spatial_surr, temp_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
            INPUT FORMATS:
            Emissions: EMFAC2014EmissionsData
                            emis_data[region][date string] = EmissionsTable
                            EmissionsTable[EIC][pollutant] = value
            Spatial Surrogates: SpatialSurrogateData[region][veh][act] = SpatialSurrogate()
            Temporal Surrogates: {'diurnal': {}, 'dow': {}}
            OUTPUT FORMAT:
            ScaledEmissions: data[region][date][hr][eic] = SparseEmissions
                                SparseEmissions[pollutant][(grid, cell)] = value
            NOTE: This function is a generator and will `yield` emissions file-by-file.
        """
        today = deepcopy(self.base_start_date)

        # loop through all the dates in the period
        while today <= self.base_end_date:
            # find the DOW
            date = today.strftime(self.date_format)
            today += timedelta(days=1)
            if date[5:] in find_holidays(self.base_year):
                dow_num = 7
                dow = 'holi'
            else:
                by_date = str(self.base_year) + date[4:]
                dow_num = dt.strptime(by_date, self.date_format).weekday()
                dow = DOW[dt.strptime(by_date, self.date_format).weekday()]

            # if not by sub-region, create emissions object
            if not self.by_region:
                e = ScaledEmissions()

            for region in self.regions:
                if date not in emissions.data[region]:
                    continue

                # if by sub-area, create emissions object
                if self.by_region:
                    e = ScaledEmissions()

                # apply DOW factors (this line is long for performance reasons)
                emis_table = self._apply_factors(deepcopy(emissions.data[region][date]),
                                                 temp_surr['dow'][region][dow])

                # find diurnal factors by hour
                factors_by_hour = temp_surr['diurnal'][region][dow]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[region]

                # loop through each hour of the day
                for hr in xrange(24):
                    # apply diurnal, then spatial profiles (this line long for performance reasons)
                    emis_dict = self._apply_spatial_surrs(self._apply_factors(deepcopy(emis_table),
                                                                              factors_by_hour[hr]),
                                                          spatial_surrs, region, dow_num, hr)

                    for eic, sparse_emis in emis_dict.iteritems():
                        e.set(region, date, hr + 1, self.eic_reduce(eic), sparse_emis)

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
        _ = f.readline()

        for line in f.xreadlines():
            # parse line
            ln = line.strip().split(',')
            poll = int(ln[10])
            if poll not in [co_id, nh3_id]:
                continue
            eic = int(ln[9])
            val = np.float32(ln[11])
            ab = ln[2]
            county = int(ln[1])
            district = ln[3]
            if (ab, county, district) not in self.reverse_regions:
                continue
            region = self.reverse_regions[(ab, county, district)]

            # fill data structure
            if region not in inv:
                inv[region] = defaultdict(np.float32)
            if eic not in inv[region]:
                inv[region][eic] = {co_id: np.float32(0.0), nh3_id: np.float32(0.0)}
            # fill in emissions values
            inv[region][eic][poll] += val
        f.close()

        # create fractions
        for region in inv:
            for eic in inv[region]:
                co = inv[region][eic][co_id]
                if not co:
                    inv[region][eic] = np.float32(0.0)
                else:
                    nh3 = inv[region][eic][nh3_id]
                    inv[region][eic] = nh3 / co

        return inv

    def _apply_factors(self, emissions_table, factors):
        """ Apply DOW or diurnal factors to an emissions table, altering the table.
            Date Types:
            EmissionsTable[EIC][pollutant] = value
            factors = {'LD': 1.0, 'LM': 0.5, 'HH': 0.0, ...}
        """
        eics2delete = []
        for eic in emissions_table:
            factor = factors[self.eic_info[eic][0]]
            if factor:
                emissions_table[eic].update((x, y * factor) for x, y in emissions_table[eic].items())
            else:
                eics2delete.append(eic)

        # don't bother with EICs if they have no emissions
        for eic in eics2delete:
            del emissions_table[eic]

        return emissions_table

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region, dow=2, hr=0):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatial_surrs[label] = SpatialSurrogate()
                                   SpatialSurrogate[(grid, cell)] = fraction
            output: {EIC: SparseEmissions[pollutant][(grid, cell)] = value}
        """
        e = {}

        # loop through each on-road EIC
        for eic in emis_table:
            se = SparseEmissions(self.nrows, self.ncols)
            label = self.eic_info[eic][1]

            # check if the surrogate is by period
            if label not in spatial_surrs:
                label += '_' + str(hr)

            # if not value or act not in spatial_surrs:
            if label not in spatial_surrs:
                continue

            # add emissions to sparse grid
            for poll, value in emis_table[eic].iteritems():
                for cell, fraction in spatial_surrs[label].iteritems():
                    se.add(poll, cell, value * fraction)

            # add NH3, based on CO fractions
            #nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, np.float32(0.0))
            #if 'CO' in emis_table[eic] and nh3_fraction:
                #value = emis_table[eic]['CO']
                #for cell, fraction in spatial_surrs[label].iteritems():
                    #se.add('NH3', cell, value * fraction * nh3_fraction)

            e[eic] = se

        return e
