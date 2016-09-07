
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar
import sys
from src.core.emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from src.core.eic_utils import eic_reduce
from src.emissions.sparce_emissions import SparceEmissions


class Emfac2CmaqScaler(EmissionsScaler):

    CALVAD_TYPE = [1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1,
                   1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 1, 3, 1]
    DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}

    def __init__(self, config, position):
        super(Emfac2CmaqScaler, self).__init__(config, position)
        self.eic_reduce = eic_reduce(self.config['Output']['eic_precision'])
        self.eic2dtim4 = self.config.eval_file('Surrogates', 'eic2dtim4')
        self.county_to_gai = self.config.eval_file('Output', 'county_to_gai')
        self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])
        self.gspro_file = self.config['Output']['gspro_file']
        self.gsref_file = self.config['Output']['gsref_file']
        self.weight_file = self.config['Output']['weight_file']
        self.gspro = {}
        self.gsref = {}
        self.groups = {}
        self.num_species = 0

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
        # Read speciation profiles & molecular weight files
        self._load_weight_file()
        self._load_gsref()
        self._load_gspro()

        # find start date
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
                dow = Emfac2CmaqScaler.DOW[dt.strptime(by_date, self.date_format).weekday()]

            # create a statewide emissions object
            e = ScaledEmissions()

            for region in self.regions:
                if date not in emissions.data[region]:
                    continue

                # apply CalVad DOW factors (this line is long for performance reasons)
                emis_table = self._apply_factors(deepcopy(emissions.data[region][date]),
                                                 temp_surr['dow'][region][dow])

                # find diurnal factors by hour
                factors_by_hour = temp_surr['diurnal'][region][dow]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[region]

                # loop through each hour of the day
                for hr in xrange(24):
                    # apply diurnal, then spatial profiles (this line long for performance reasons)
                    sparce_emis = self._apply_spatial_surrs(self._apply_factors(deepcopy(emis_table),
                                                                                factors_by_hour[hr]),
                                                            spatial_surrs, region)
                    e.set(-999, date, hr + 1, -999, sparce_emis)

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
            eic = int(ln[-3])
            val = float(ln[-1])
            county = int(ln[1])
            regions = self.county_to_gai[county]
            for region in regions:
                # fill data structure
                if region not in inv:
                    inv[region] = defaultdict(float)
                if eic not in inv[region]:
                    inv[region][eic] = {co_id: 0.0, nh3_id: 0.0}
                # fill in emissions values
                inv[region][eic][poll] += val
        f.close()

        # create fractions
        for region in inv:
            for eic in inv[region]:
                co = inv[region][eic][co_id]
                if co == 0.0:
                    inv[region][eic] = 0.0
                else:
                    nh3 = inv[region][eic][nh3_id]
                    inv[region][eic] = nh3 / co

        return inv

    def _apply_factors(self, emissions_table, factors):
        """ Apply CalVad DOW or diurnal factors to an emissions table, altering the table.
            Date Types:
            EmissionsTable[EIC][pollutant] = value
            factors = [ld, lm, hh, sbus]
        """
        zeros = []
        # scale emissions table for diurnal factors
        for eic in emissions_table:
            factor = factors[self.CALVAD_TYPE[self.eic2dtim4[eic][0]]]
            if factor == 0.0:
                zeros.append(eic)
            else:
                emissions_table[eic].update((x, y * factor) for x, y in emissions_table[eic].items())

        # remove zero-emissions EICs
        for eic in zeros:
            del emissions_table[eic]

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
        se = SparceEmissions()

        # grid emissions, by EIC
        for eic in emis_table:
            veh, act = self.eic2dtim4[eic]

            # speciate by pollutant, while gridding
            for poll, value in emis_table[eic].iteritems():
                POLL = poll.upper()
                if POLL == 'PM':
                    label = self.gsref[int(eic)]['PM']
                elif POLL == 'TOG':
                    label = self.gsref[int(eic)]['TOG']
                elif POLL == 'NOX':
                    label = 'DEFNOX'
                else:
                    label = POLL

                gspro_label = self.gspro[label][POLL]
                groups = self.groups[POLL]['species']

                # loop through each grid cell
                for index,species in enumerate(groups):
                    speciated_value = value * gspro_label[index]
                    for cell, cell_fraction in spatial_surrs[veh][act].iteritems():
                        se[cell][species] += speciated_value * cell_fraction

            # add NH3, based on NH3/CO fractions
            nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, 0.0)
            if 'co' in emis_table[eic] and nh3_fraction:
                nh3_value = emis_table[eic]['co'] * nh3_fraction
                for cell, cell_fraction in spatial_surrs[veh][act].iteritems():
                    se[cell]['NH3'] += nh3_value * cell_fraction

        return se

    def _find_holidays(self):
        ''' Using Pandas calendar, find all 10 US Federal Holidays,
            plus California's Cesar Chavez Day (March 31).
        '''
        yr = str(self.base_year)
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()

        return [d.strftime('%m-%d') for d in holidays] + ['03-31']

    def _load_gsref(self):
        ''' load the gsref file
            File Format: eic,profile,group
            0,CO,CO
            0,NH3,NH3
            0,SOx,SOX
            0,DEFNOx,NOX
            0,900,PM
        '''
        self.gsref = {}

        f = open(self.gsref_file, 'r')
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) != 3:
                continue
            eic = int(ln[0])
            profile = ln[1].upper()
            group = ln[2].upper()
            if eic not in self.gsref:
                self.gsref[eic] = {}
            self.gsref[eic][group] = profile

        f.close()

    def _load_weight_file(self):
        """ load molecular weight file
            File Format:
            NO          30.006      NOX    moles/s
            NO2         46.006      NOX    moles/s
            HONO        47.013      NOX    moles/s
        """
        # read molecular weight text file
        fin = open(self.weight_file,'r')
        lines = fin.read()
        fin.close()

        # read in CSV or Fortran-formatted file
        lines = lines.replace(',', ' ')
        lines = lines.split('\n')

        self.groups = {}
        # loop through file lines and
        for line in lines:
            # parse line
            columns = line.rstrip().split()
            if not columns:
                continue
            species = columns[0].upper()
            weight = float(columns[1])
            group = columns[2].upper()

            # file output dict
            if group not in self.groups:
                self.groups[group] = {'species': []}
            self.groups[group]['species'].append(species)

        # convert weight list to numpy.array
        for grp in self.groups:
            self.groups[grp]['species'] = np.array(self.groups[grp]['species'], dtype=np.dtype('a8'))

        # calculate the number of species total
        self.num_species = 0
        for group in self.groups:
            self.num_species += len(self.groups[group]['species'])

    def _load_gspro(self):
        ''' load the gspro file
            File Format:  group, pollutant, species, mole fraction, molecular weight=1, mass fraction
            1,TOG,CH4,3.1168E-03,1,0.0500000
            1,TOG,ALK3,9.4629E-03,1,0.5500000
            1,TOG,ETOH,5.4268E-03,1,0.2500000
        '''
        self.gspro = {}

        f = open(self.gspro_file, 'r')
        for line in f.xreadlines():
            # parse line
            ln = line.rstrip().split(',')
            profile = ln[0].upper()
            group = ln[1].upper()
            if group not in self.groups:
                sys.exit('ERROR: Group ' + group + ' not found in molecular weights file.')
            pollutant = ln[2].upper()
            try:
                poll_index = list(self.groups[group]['species']).index(pollutant)
            except ValueError:
                # we don't care about CH4
                pass
            # start filling output dict
            if profile not in self.gspro:
                self.gspro[profile] = {}
            if group not in self.gspro[profile]:
                self.gspro[profile][group] = np.zeros(len(self.groups[group]['species']),
                                                      dtype=np.float32)
            self.gspro[profile][group][poll_index] = float(ln[5])

        f.close()
