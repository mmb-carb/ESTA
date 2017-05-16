
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import sys
from src.core.date_utils import DOW, find_holidays, find_season
from src.core.emissions_scaler import EmissionsScaler
from scaled_emissions import ScaledEmissions
from src.emissions.sparse_emissions import SparseEmissions


class Emfac2CmaqScaler(EmissionsScaler):

    CSTDM_HOURS = ['off', 'off', 'off', 'off', 'off', 'off',   # off peak: 6 AM to 10 AM
                    'am',  'am',  'am',  'am',  'mid', 'mid',  # midday:   10 AM to 3 PM
                    'mid', 'mid', 'mid', 'pm',  'pm',  'pm',   # pm peak:  3 PM to 7 PM
                    'pm',  'off', 'off', 'off', 'off', 'off']  # off peak: 7 PM to 6 AM
    CALVAD_TYPE = [0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 0, 3, 0,
                   0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 0, 3, 0]
    DOWS = ['_monday_', '_tuesday_', '_wednesday_', '_thursday_', '_friday_',
            '_saturday_', '_sunday_', '_holiday_']
    STONS_HR_2_G_SEC = np.float32(251.99583333333334)

    def __init__(self, config, position):
        super(Emfac2CmaqScaler, self).__init__(config, position)
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.reverse_regions = dict(((d['air_basin'], d['county'], d['district']), g) for g,d in self.region_info.iteritems())
        self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.is_smoke4 = 'smoke4' in self.config['Surrogates']['spatial_loaders'].lower()
        self.region_boxes = self.config.eval_file('Surrogates', 'region_boxes')  # bounds are inclusive
        self.summer_gsref = Emfac2CmaqScaler.load_gsref(self.config['Output']['summer_gsref_file'])
        self.winter_gsref = Emfac2CmaqScaler.load_gsref(self.config['Output']['winter_gsref_file'])
        self.gsref = self.summer_gsref  # to be used, during the run, to point to the right file
        self.species = set()
        self.gspro = self.load_gspro(self.config['Output']['gspro_file'])
        self.diesel_nox = self.load_nox_file(self.config['Output']['nox_file'])
        self.region_info = self.config.eval_file('Regions', 'region_info')

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
            ScaledEmissions: data[region][date][hr][eic] = SparseEmissions
                             SparseEmissions[pollutant][(grid, cell)] = value
            NOTE: This function is a generator and will `yield` emissions file-by-file.
        """
        self._load_species(emissions)

        # find start date
        today = dt(self.start_date.year, self.start_date.month, self.start_date.day)

        # loop through all the dates in the period
        while today <= self.end_date:
            # use the speciation from the correct season
            if find_season(today).lower() == 's':
                self.gsref = self.summer_gsref
            else:
                self.gsref = self.winter_gsref
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

            # create a statewide emissions object
            e = self._prebuild_scaled_emissions(date)

            for region in self.regions:
                if date not in emissions.data[region]:
                    continue

                # handle region bounding box (limits are inclusive: {'lat': (51, 92), 'lon': (156, 207)})
                box = self.region_boxes[region]

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
                    sparse_emis = self._apply_spatial_surrs(self._apply_factors(deepcopy(emis_table),
                                                                                factors_by_hour[hr]),
                                                            spatial_surrs, region, box, dow_num, hr)
                    e.add_subgrid_nocheck(-999, date, hr + 1, -999, sparse_emis, box)

            yield e

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region, box, dow=2, hr=0):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatial_surrs[veh][act] = SpatialSurrogate()
                                      SpatialSurrogate[(grid, cell)] = fraction
            region_box: {'lat': (51, 92), 'lon': (156, 207)}
            output: {EIC: SparseEmissions[pollutant][(grid, cell)] = value}
        """
        zero = np.float32(0.0)

        # find HD diesel NOx fractions for this air basin and year
        ab = 'default'
        yr = 'default'
        if self.region_info[region]['air_basin'] in self.diesel_nox:
            ab = self.region_info[region]['air_basin']
        if self.start_date.year in self.diesel_nox[ab]:
            yr = self.start_date.year
        hono_fract, no_fract, no2_fract = self.diesel_nox[ab][yr]

        # examine bounding box
        min_lat = box['lat'][0]
        min_lon = box['lon'][0]
        num_rows = box['lat'][1] - box['lat'][0] + 1
        num_cols = box['lon'][1] - box['lon'][0] + 1

        # pre-build emissions object
        se = self._prebuild_sparse_emissions(num_rows, num_cols)

        # grid emissions, by EIC
        for eic in emis_table:
            # fix VMT activity according to Calvad periods
            veh, act, _ = self.eic_info[eic]
            if self.is_smoke4 and act[:3] in ['vmt', 'vht']:
                act += self.DOWS[dow] + self.CSTDM_HOURS[hr]

            # build default spatial surrogate for this EIC
            ss = np.zeros((num_rows, num_cols), dtype=np.float32)
            try:
                for cell, cell_fraction in spatial_surrs[veh][act].iteritems():
                    ss[(cell[0] - min_lat, cell[1] - min_lon)] = cell_fraction
            except KeyError:
                err = ('Spatial Surrogate grid cell (%d, %d) found outside of bounding box' + \
                       ' %s in region %d.') % (cell[0], cell[1], box, region)
                raise KeyError(err)

            # find all relevant species and molecular weights for this EIC
            species_data = self.gspro['default'].copy()
            for group, profile in self.gsref[eic].iteritems():
                species_data[group] = self.gspro[profile][group]

            # adjust NOx for HD diesel vehicles
            if eic in self.HD_DSL_CATS:
                species_data['NOX'] = {'HONO': {'mass_fract': hono_fract, 'weight': np.float32(47.013)},
                                       'NO':   {'mass_fract': no_fract,   'weight': np.float32(30.006)},
                                       'NO2':  {'mass_fract': no2_fract,  'weight': np.float32(46.006)}}

            # speciate by pollutant, while gridding
            for poll, value in emis_table[eic].iteritems():
                if not value:
                    continue

                # loop through each species in this pollutant group
                for spec in species_data[poll.upper()]:  # TODO: Make all species names uppercase everywhere in ESTA
                    spec_value = value * species_data[poll.upper()][spec]['mass_fract'] * self.STONS_HR_2_G_SEC / species_data[poll.upper()][spec]['weight']

                    # loop through each grid cell
                    se.add_grid_nocheck(spec, ss * spec_value)

            # add NH3, based on NH3/CO fractions
            if 'co' in emis_table[eic]:
                nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, zero)
                if not nh3_fraction:
                    continue

                nh3_fraction *= (self.STONS_HR_2_G_SEC / self.gspro['default']['NH3']['NH3']['weight'])
                se.add_grid_nocheck('NH3', ss * (emis_table[eic]['co'] * nh3_fraction))

        return se

    def _apply_factors(self, emissions_table, factors):
        """ Apply CalVad DOW or diurnal factors to an emissions table, altering the table.
            Date Types:
            EmissionsTable[EIC][pollutant] = value
            factors = [ld, lm, hh, sbus]
        """
        zeros = []
        # scale emissions table for diurnal factors
        for eic in emissions_table:
            factor = factors[self.CALVAD_TYPE[self.eic_info[eic][0]]]
            if not factor:
                zeros.append(eic)
            else:
                emissions_table[eic].update((x, y * factor) for x, y in emissions_table[eic].items())

        # remove zero-emissions EICs
        for eic in zeros:
            del emissions_table[eic]

        return emissions_table

    def _prebuild_scaled_emissions(self, date):
        """ Pre-Build a ScaledEmissions object, for the On-Road NetCDF case, where:
            region = -999
            EIC = -999
            And each pollutant grid is pre-built in the SparseEmissions object.
        """
        e = ScaledEmissions()
        se = self._prebuild_sparse_emissions(self.nrows, self.ncols)
        for hr in xrange(1, 25):
            e.set(-999, date, hr, -999, se.copy())

        return e

    def _prebuild_sparse_emissions(self, nrows, ncols):
        ''' pre-process to add all relevant species to SparseEmissions object '''
        se = SparseEmissions(nrows, ncols)
        for spec in self.species:
            se.add_poll(spec)

        return se

    def _load_species(self, emissions):
        """ find all the pollutant species that will matter for this simulation """
        # first, find all the EICs in the input emissions
        eics = set()
        for region in emissions.data:
            for date in emissions.data[region]:
                eics.update(set(emissions.data[region][date].keys()))

        # now find all the species we care about for this run
        self.species = set(['CO', 'HONO', 'NH3', 'NO', 'NO2', 'SO2', 'SULF'])
        for eic in eics:
            if eic not in self.gsref:
                print('ERROR: EIC MISSING FROM GSREF: ' + str(eic))
                continue
            for group, profile in self.gsref[eic].iteritems():
                for species in self.gspro[profile][group]:
                    self.species.add(species)

    def _read_nh3_inventory(self, inv_file):
        """ read the NH3/CO values from the inventory and generate the NH3/CO fractions
            File format:
            fyear,co,ab,dis,facid,dev,proid,scc,sic,eic,pol,ems
            2012,33,SC,SC,17953,1,11,39000602,3251,5007001100000,42101,5.418156170044
        """
        co_id = 42101
        nh3_id = 7664417
        inv = {}
        f = open(inv_file, 'r')
        header = f.readline()

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

    @staticmethod
    def load_gsref(file_path):
        ''' load the gsref file
            File Format: eic,profile,group
            0,CO,CO
            0,NH3,NH3
            0,SOx,SOX
            0,DEFNOx,NOX
            0,900,PM
        '''
        gsref = {}

        f = open(file_path, 'r')
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) != 3:
                continue
            eic = int(ln[0])
            profile = ln[1].upper()
            group = ln[2].upper()
            if eic not in gsref:
                gsref[eic] = {}
            gsref[eic][group] = profile

        f.close()
        return gsref

    @staticmethod
    def load_gspro(file_path):
        ''' load the gspro file
            File Format:  profile, group, species, mole fraction, molecular weight=1, mass fraction
            1,TOG,CH4,3.1168E-03,1,0.0500000
            1,TOG,ALK3,9.4629E-03,1,0.5500000
            1,TOG,ETOH,5.4268E-03,1,0.2500000
        '''
        special_profile = ['CO', 'DEFNOX', 'NH3', 'SOX']
        gspro = {}

        f = open(file_path, 'r')
        for line in f.xreadlines():
            # parse line
            ln = line.rstrip().split(',')
            profile = ln[0].upper()
            group = ln[1].upper()
            species = ln[2].upper()

            # handle PM and TOG profiles differently
            if profile in special_profile:
                profile = 'default'

            # start filling output dict
            if profile not in gspro:
                gspro[profile] = {}
            if group not in gspro[profile]:
                gspro[profile][group] = {}

            if profile == 'default':
                gspro[profile][group][species] = {'mass_fract': np.float32(ln[5]),
                                                  'weight': np.float32(ln[4])}
            else:
                gspro[profile][group][species] = {'mass_fract': np.float32(ln[5]),
                                                  'weight': np.float32(ln[5]) / np.float32(ln[3])}

        f.close()
        return gspro

    @staticmethod
    def load_nox_file(file_path):
        """ Read a NOx-speciation file that contains the mass fractions of NO, NO2, and HONO
            for different airbasins and years.  The first line is for default values.
            The file format is:
            Air_Basin,Year,NO,NO2,HONO
            default,default,0.574,0.1,0.0203640715
            SC,2005,0.573913,0.1,0.0205003819
        """
        # open file and dump header
        f = open(file_path, 'r')
        _ = f.readline()

        # read off the default line
        no, no2, hono = [float(v) for v in f.readline().rstrip().split(',')[2:5]]
        diesel_nox = defaultdict(lambda: defaultdict(lambda: np.array([hono, no, no2], dtype=np.float32)))

        # parse each line in the rest of the file, with no defaults
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            ab = ln[0]
            yr = int(ln[1])
            no = float(ln[2])
            no2 = float(ln[3])
            hono = float(ln[4])
            diesel_nox[ab][yr] = np.array([hono, no, no2], dtype=np.float32)

        f.close()
        return diesel_nox

    # Heavy-Duty Diesel vehicle categories
    HD_DSL_CATS = set([217, 220, 408, 420, 508, 520, 617, 620, 717, 720, 74076412100000, 74476112100000,
         74476112107000, 74476112107001, 74476112107004, 74476112107005, 74476112107006, 74476112107007,
         74476112107008, 74476112107009, 74476112107010, 74476112107011, 74476112107012, 74476412100000,
         74476412107000, 74476412107001, 74476412107004, 74476412107005, 74476412107006, 74476412107007,
         74476412107008, 74476412107009, 74476412107010, 74476412107011, 74476412107012, 74476512100000,
         74476512107000, 74476512107001, 74476512107004, 74476512107005, 74476512107006, 74476512107007,
         74476512107008, 74476512107009, 74476512107010, 74476512107011, 74476512107012, 74676112100000,
         74676112107013, 74676112107016, 74676112107017, 74676112107018, 74676112107019, 74676112107020,
         74676112107021, 74676112107024, 74676112107025, 74676112107026, 74676112107027, 74676112107028,
         74676112107029, 74676112107030, 74676112107031, 74676112107032, 74676412100000, 74676412107013,
         74676412107016, 74676412107017, 74676412107018, 74676412107019, 74676412107020, 74676412107021,
         74676412107024, 74676412107025, 74676412107026, 74676412107027, 74676412107028, 74676412107029,
         74676412107030, 74676412107031, 74676412107032, 74676512100000, 74676512107013, 74676512107016,
         74676512107017, 74676512107018, 74676512107019, 74676512107020, 74676512107021, 74676512107024,
         74676512107025, 74676512107026, 74676512107027, 74676512107028, 74676512107029, 74676512107030,
         74676512107031, 74676512107032, 76076112100000, 76076412100000, 77276112100000, 77276412100000,
         77276512100000, 77876112100000, 77876412100000, 77876512100000, 77976112100000, 77976412100000,
         77976512100000])
