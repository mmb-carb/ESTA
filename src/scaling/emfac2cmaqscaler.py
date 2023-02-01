
from collections import defaultdict
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
from src.core.date_utils import DOW, find_holidays
from src.core.emissions_scaler import EmissionsScaler
from src.scaling.scaled_emissions import ScaledEmissions
from src.emissions.sparse_emissions import SparseEmissions
from src.surrogates.flexibletemporalloader import CALVAD_TYPE


class Emfac2CmaqScaler(EmissionsScaler):

    PERIODS_BY_HR = ['OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF',  # off peak: 6 AM to 10 AM
                     'AM',  'AM',  'AM',  'AM',  'MID', 'MID',  # midday:   10 AM to 3 PM
                     'MID', 'MID', 'MID', 'PM',  'PM',  'PM',   # pm peak:  3 PM to 7 PM
                     'PM',  'OFF', 'OFF', 'OFF', 'OFF', 'OFF']  # off peak: 7 PM to 6 AM
    STONS_HR_2_G_SEC = np.float32(251.99583333333334)

    def __init__(self, config, position):
        super(Emfac2CmaqScaler, self).__init__(config, position)
        self.eic_info = self.config.eval_file('Surrogates', 'eic_info')
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.reverse_regions = dict(((d['air_basin'], d['county'], d['district']), g) for g,d in self.region_info.iteritems())
        #self.nh3_fractions = self._read_nh3_inventory(self.config['Scaling']['nh3_inventory'])
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.region_boxes = self.config.eval_file('Surrogates', 'region_boxes')  # bounds are inclusive
        self.summer_gsref = Emfac2CmaqScaler.load_gsref(self.config['Output']['summer_gsref_file'])
        self.winter_gsref = Emfac2CmaqScaler.load_gsref(self.config['Output']['winter_gsref_file'])
        self.gsref = self.summer_gsref  # to be used, during the run, to point to the right file
        self.species = set()
        self.gspro = self.load_gspro(self.config['Output']['gspro_file'])
        self.diesel_nox = self.load_nox_file(self.config['Output']['nox_file'])
        self.month2season = self.read_month_to_season()

    def scale(self, emissions, spatial_surr, temp_surr):
        """ Master method to scale emissions using spatial and temporal surrogates.
            INPUT FORMATS:
            Emissions: EMFAC2014EmissionsData
                       emis_data[region][date string] = EmissionsTable
                       EmissionsTable[EIC][pollutant] = value
            Spatial Surrogates: SpatialSurrogateData[region][label] = SpatialSurrogate()
            Temporal Surrogates: {'diurnal': {}, 'dow': {}}
            OUTPUT FORMAT:
            ScaledEmissions: data[region][date][hr][eic] = SparseEmissions
                             SparseEmissions[pollutant][(grid, cell)] = value
            NOTE: This function is a generator and will `yield` emissions file-by-file.
        """
        self._load_species(emissions)

        # find start date
        today = dt(self.base_year, self.start_date.month, self.start_date.day)
        jday = today.strftime('%Y%j')

        # loop through all the dates in the period
        while today <= self.base_end_date:
            # find the DOW
            date = today.strftime(self.date_format)
            today += timedelta(days=1)
            if date[5:] in find_holidays(self.base_year):
                dow = 'holi'
            else:
                by_date = str(self.base_year) + date[4:]
                dow = DOW[dt.strptime(by_date, self.date_format).weekday()]

            # create a statewide emissions object
            e = self._prebuild_scaled_emissions(date)

            for region in self.regions:
                if date not in emissions.data[region]:
                    continue

                # use the speciation from the correct season
                if self.month2season[region][today.month] == 's':
                    self.gsref = self.summer_gsref
                else:
                    self.gsref = self.winter_gsref

                # handle region bounding box (limits are inclusive: {'lat': (51, 92), 'lon': (156, 207)})
                box = self.region_boxes[region]

                # apply DOW factors (this line is long for performance reasons)
                emis_table = self._apply_factors(deepcopy(emissions.data[region][date]),
                                                 temp_surr['dow'][region][dow], temp_surr['doy'][region][jday]['day'])

                # find diurnal factors by hour
                factors_by_hour = temp_surr['diurnal'][region][dow]

                # hd diurnal factors by hour
                hd_factors_by_hour = temp_surr['doy'][region][jday]

                # pull today's spatial surrogate
                spatial_surrs = spatial_surr.data[region]

                # loop through each hour of the day
                for hr in xrange(24):
                    sparse_emis = self._apply_spatial_surrs(self._apply_factors(emis_table, factors_by_hour[hr], hd_factors_by_hour[hr]),
                                                            spatial_surrs, region, box, hr)
                    e.add_subgrid_nocheck(-999, date, hr + 1, -999, sparse_emis, box)

            yield e

    def _apply_spatial_surrs(self, emis_table, spatial_surrs, region, box, hr=0):
        """ Apply the spatial surrogates for each hour to this EIC and create a dictionary of
            sparely-gridded emissions (one for each eic).
            Data Types:
            EmissionsTable[EIC][pollutant] = value
            spatial_surrs[label] = SpatialSurrogate()
                                   SpatialSurrogate[(grid, cell)] = fraction
            region_box: {'lat': (51, 92), 'lon': (156, 207)}
            output: {EIC: SparseEmissions[pollutant][(grid, cell)] = value}
        """
        # determine the region for HD diesel NOx
        r = 'default'
        if str(region) in self.diesel_nox:
            r = str(region)
        # determine the year for HD diesel NOx
        yr = self.start_date.year
        if self.start_date.year not in self.diesel_nox[r]:
            yr = min(self.diesel_nox[r].iterkeys(), key=lambda y: abs(y - self.start_date.year))

        hono_fract, no_fract, no2_fract = self.diesel_nox[r][yr]

        # examine bounding box
        min_lat = box['lat'][0]
        min_lon = box['lon'][0]
        num_rows = box['lat'][1] - box['lat'][0] + 1
        num_cols = box['lon'][1] - box['lon'][0] + 1

        # pre-build emissions object
        se = self._prebuild_sparse_emissions(num_rows, num_cols)

        # grid emissions, by EIC
        for eic in emis_table:
            label = self.eic_info[eic][1]

            # check if the surrogate is by period
            if label not in spatial_surrs:
                label += '_' + str(hr)

            # build default spatial surrogate for this EIC
            ss = np.zeros((num_rows, num_cols), dtype=np.float32)
            try:
                for cell, cell_fraction in spatial_surrs[label].iteritems():
                    ss[cell[0] - min_lat, cell[1] - min_lon] = cell_fraction
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
            for pol, value in emis_table[eic].iteritems():
                if not value:
                    continue

                # loop through each species in this pollutant group
                poll = pol.upper()
                for spec, spec_data in species_data[poll].iteritems():
                    se.add_grid_nocheck(spec, (value * spec_data['mass_fract'] * self.STONS_HR_2_G_SEC / spec_data['weight']) * ss)

            # add NH3, based on NH3/CO fractions
            #if 'CO' in emis_table[eic]:
            #    nh3_fraction = self.nh3_fractions.get(region, {}).get(eic, 0)
            #    if not nh3_fraction:
            #        continue

                # add NH3 based on its relation to CO
                #se.add_grid_nocheck('NH3', (emis_table[eic]['CO'] * nh3_fraction * (self.STONS_HR_2_G_SEC / self.gspro['default']['NH3']['NH3']['weight'])) * ss)

        return se

    def _apply_factors(self, emissions_table, factors, hd_factors):
        """ Apply DOW or diurnal factors to an emissions table, altering the table.
            Date Types:
            EmissionsTable[EIC][pollutant] = value
            factors = {'LD': 1.0, 'LM': 0.5, 'HH': 0.0, ...}
        """
        new_emis_table = {}

        # loop through all EICs and add time-scaled data
        for eic, emis in emissions_table.iteritems():
            if eic in self.HD_eic:
                factor = hd_factors
            else:
                factor = factors[CALVAD_TYPE[self.eic_info[eic][0]]]

            if factor:
                # ignore EICs with zerod emissions
                new_emis_table[eic] = dict((p, v * factor) for p, v in emis.iteritems())

        return new_emis_table

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
        if self.config['Output']['dpmout']:
            self.species = set(['CO', 'HONO', 'NH3', 'NO', 'NO2', 'SO2', 'SULF', 'PM10', 'PM25', 'DPM10', 'DPM25', 'DPM'])
        else:
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

    def read_month_to_season(self):
        ''' create a region-specific month-to-season mapping,
            from a given CSV file
        '''
        # if not file is provided, use a default month-to-season mapping
        if 'month_to_season' not in self.config['Scaling']:
            by_month = ['w', 'w', 'w', 's', 's', 's', 's', 's', 's', 'w', 'w', 'w']
            return defaultdict(lambda: dict((i + 1, l) for i, l in enumerate(by_month)))

        # read month-to-season CSV
        file_path = self.config['Scaling']['month_to_season']
        lines = open(file_path, 'r').readlines()

        # create output month-to-season dictionary, using the first line as default
        m2s = defaultdict(lambda: dict((i + 1, l) for i, l in enumerate(lines[1].rstrip().lower().split(',')[1:])))

        # add a month-to-season mapping for each region
        for i in xrange(2, len(lines)):
            ln = lines[i].rstrip().lower().split(',')
            m2s[int(ln[0])] = dict((i + 1, l) for i, l in enumerate(ln[1:]))

        return m2s

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
        special_profile = ['CO', 'DEFNOX', 'NH3', 'SOX', 'PM10', 'PM25', 'DPM10', 'DPM25', 'DPM']
        gspro = {}

        f = open(file_path, 'r')
        for line in f.xreadlines():
            # parse line
            ln = line.rstrip().split(',')
            profile = ln[0].upper()
            group = ln[1].upper()
            species = ln[2].upper()
            if np.float32(ln[3]) == 0.:
                continue

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
            region = ln[0]
            yr = int(ln[1])
            no = float(ln[2])
            no2 = float(ln[3])
            hono = float(ln[4])
            diesel_nox[region][yr] = np.array([hono, no, no2], dtype=np.float32)

        f.close()
        return diesel_nox


    # Heavy-Duty Diesel vehicle categories
    HD_DSL_CATS = [72876512107072, 72876512107074, 72776112107050, 72776412107045, 72776112107045, 77576112107201, 72776412107050, 72876112107076, 72776512107062, 72776412107053, 72776112107061, 72776512107044, 72776112107046, 72776412107043, 72776112107054, 72876112107079, 72876512107073, 72876512107079, 72876112107073, 72876412107070, 72876112107078, 72776412107054, 72776512107048, 72776112107056, 72876412107067, 72776512107056, 72876112107068, 72876412107039, 72876412107071, 72876512107071, 72776512107061, 72776412107059, 72876112107071, 72776112107063, 72776512107063, 72776412107064, 72776112107041, 72876512107076, 72776512107041, 72776412107047, 72876412107074, 72776512107045, 72776512107050, 72776412107051, 72776512107058, 72776112107047, 72776112107057, 72776412107058, 72776512107065, 72876512107069, 72776412107065, 72776512107043, 72776412107044, 72776512107060, 72776112107043, 72776512107054, 72876112107067, 72776512107055, 72876412107079, 72876512107067, 77576512107201, 72876112107075, 72776512107046, 72876412107075, 72776512107049, 72776412107056, 72776412107061, 72876412107078, 72776512107059, 72876412107068, 72876412107076, 72776412107057, 72776412107063, 72776512107064, 72876112107072, 72776512107052, 72776412107041, 72776112107060, 72776112107062, 72776112107052, 72776512107051, 72776112107058, 72776112107055, 72776112107051, 72876112107077, 72776512107053, 72776412107062, 72776112107042, 72876412107069, 72876412107073, 72876512107077, 72776512107047, 72876112107074, 72776412107060, 72776112107044, 72876412107077, 72776412107055, 72776412107052, 72776412107048, 72876512107070, 72876112107070, 72776412107046, 72776112107059, 72876512107075, 77576412107201, 72776412107049, 72776112107049, 72876512107078, 72776112107048, 72876112107069, 72876512107068, 72776112107064, 72776112107053, 72776512107057, 72776112107065, 72776412107042, 72776512107042, 72876412107072]

    HD_eic = [72874702487077, 72876512107072, 72876512107074, 72876854107071, 77576112107201, 72876112107076, 72877354107072, 72877402487070, 72876854107075, 72876854107067, 72877402487073, 72877354107067, 72876112107079, 72876512107073, 72874854107077, 72876512107079, 72877402487074, 72874702487073, 72876602487069, 72877354107078, 72877354107074, 72876112107073, 72874702487067, 72876412107070, 72877402487072, 72873401107077, 72876112107078, 77576602487201, 72873101107071, 72874854107071, 72876412107067, 72874211007080, 72873401107072, 72876112107068, 72876412107039, 72876412107071, 72873501107067, 72876512107071, 72874302487080, 72873101107067, 72876602487073, 72873401107076, 72876854107076, 72876112107071, 72870111007080, 72873501107074, 72874854107074, 72873111007080, 72876602487068, 72876512107076, 72873411007080, 72873401107078, 72870811007080, 72876602487079, 72876412107074, 72874702487072, 72874854107067, 72874854107072, 72877402487076, 72876512107069, 72873501107071, 72874854107073, 72876602487078, 72873101107077, 72877354107071, 72876854107079, 72873101107072, 72876854107073, 72876112107067, 72876602487074, 72876412107079, 72877354107075, 72876512107067, 72877354107077, 77576512107201, 72876112107075, 72876854107069, 72876412107075, 72874702487071, 72876854107074, 72876412107078, 72874702487078, 72874554107080, 72873101107074, 72877402487077, 72872254107080, 72877354107080, 72876412107068, 72876602487072, 72873501107075, 72873101107075, 72876412107076, 72876602487076, 72876602487071, 72873401107074, 72873501107078, 72876854107068, 72874702487076, 72876112107072, 72870611007080, 72873611007080, 72874702487074, 72874854107076, 72877402487079, 72873401107073, 72876854107078, 72877402487071, 77576854107201, 72873401107071, 72876602487070, 72876112107077, 72877402487078, 72876412107069, 72874854107075, 72876412107073, 72876512107077, 72876854107070, 72876112107074, 72876412107077, 72877354107073, 72873501107077, 72871211007080, 72876602487075, 72876512107070, 72876854107077, 72873501107073, 72876112107070, 72876512107075, 72876602487077, 72871411007080, 77576412107201, 72873401107067, 72873501107072, 72877402487067, 72872102487080, 72877402487075, 72876512107078, 72876854107072, 72873101107073, 72873501107076, 72876112107069, 72873101107076, 72873101107078, 72876512107068, 72874702487075, 72874854107078, 72877354107079, 72873401107075, 72874011007080, 72877354107070, 72877354107076, 72877402487080, 72876602487067, 72876412107072]
