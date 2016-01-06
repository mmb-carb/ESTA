
from collections import defaultdict
from datetime import datetime, timedelta
from netCDF4 import Dataset
import os
from pandas.tseries.holiday import USFederalHolidayCalendar
from pyproj import Proj
from src.core.spatial_loader import SpatialLoader
from spatial_surrogate import SpatialSurrogate
import sys
from temporal_surrogate import TemporalSurrogate


class Dtim4Loader(SpatialLoader):
    """ This class is designed to load the spatial surrogates represtented by the DTIM4 input
        link and TAZ files.
    """

    DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}

    def __init__(self, config, directory):
        super(Dtim4Loader, self).__init__(config, directory)
        self.counties = Dtim4Loader.parse_counties(self.config['Subareas']['subareas'])
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.grid_file_path = self.config['GridInfo']['grid_dot_file']
        self.lat_dot, self.lon_dot = self._read_grid_corners_file()
        self.date_format = self.config['Dates']['format']
        self.start_date = datetime.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = datetime.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.data = Dtim4SpatialData()
        self.county_boxes = eval(open(self.config['Misc']['county_boxes'], 'r').read())

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read DTIM4 road network files """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = Dtim4SpatialData()
        if not temporal_surrogates:
            temporal_surrogates = {'diurnal': Dtim4TemporalData()}

        # figure out which DOWs we need to run
        dows = self._dows_to_run()

        # loop through all the counties
        for county in self.counties:
            print('Processing county #' + str(county))
            fips = Dtim4Loader.county_to_fips(county)
            # loop through each DOW
            for dow in dows:
                # loop through the hourly files
                for hr in xrange(1, 25):
                    # build the file paths
                    link_file = os.path.join(self.directory, fips,
                                             'dtim_link_' + fips + '_' + dow + '_%02d.dat' % hr)
                    taz_file = link_file.replace('link', 'taz')

                    # read link file
                    if not os.path.exists(link_file):
                        sys.exit('Link file does not exist: ' + link_file)
                        continue
                    link_spatial_surrs, nodes = self._read_link_file(link_file, county)
                    link_temporal_surrs = Dtim4Loader.spatial_dict_to_temporal(link_spatial_surrs)

                    # read TAZ file (TAZ file needs node definitions from link file)
                    if not os.path.exists(taz_file):
                        sys.exit('TAZ file does not exist: ' + link_file)
                    taz_spatial_surrs = self._read_taz_file(taz_file, nodes)
                    taz_temporal_surrs = Dtim4Loader.spatial_dict_to_temporal(taz_spatial_surrs)

                    # add surrogate data to the correct dates
                    for date in dows[dow]:
                        spatial_surrogates.add_file(county, date, hr, link_spatial_surrs)
                        spatial_surrogates.add_file(county, date, hr, taz_spatial_surrs)
                        temporal_surrogates['diurnal'].add_file(county, date, hr, link_temporal_surrs)
                        temporal_surrogates['diurnal'].add_file(county, date, hr, taz_temporal_surrs)

        # normalize surrogates
        spatial_surrogates.surrogates()
        temporal_surrogates['diurnal'].surrogates()

        return spatial_surrogates, temporal_surrogates

    @staticmethod
    def spatial_dict_to_temporal(spatial_dict):
        """ convert a dictionary of spatial surrogtes to a dictionary of temporal surrogates """
        t = {}
        for veh, veh_data in spatial_dict.iteritems():
            t[veh] = {}
            for act, surr in veh_data.iteritems():
                t[veh][act] = sum(surr.values())
        return t

    @staticmethod
    def county_to_fips(county):
        """ This converts the county code (1 to 58) to the FIPS code. """
        return '%03d' % (2 * county - 1)

    @staticmethod
    def parse_counties(counties_str):
        """ Parse the string we get back from the subareas field """
        if '..' in counties_str:
            counties = counties_str.split('..')
            counties = range(int(counties[0]), int(counties[1]))
        else:
            counties = [int(c) for c in counties_str.split()]

        return counties

    def _dows_to_run(self):
        """ Find all the DOWs to run in the given date range """
        dows = defaultdict(list)
        holidays = self._find_holidays()
        model_year = self.start_date.year

        today = datetime(self.base_year, self.start_date.month, self.start_date.day)
        end = datetime(self.base_year, self.end_date.month, self.end_date.day)
        while today <= end:
            dow = Dtim4Loader.DOW[today.weekday()]
            if today.strftime('%m-%d') in holidays:
                dows['holi'].append(str(model_year) + today.strftime(self.date_format)[4:])
            else:
                dows[dow].append(str(model_year) + today.strftime(self.date_format)[4:])
            today += timedelta(days=1)

        return dows

    def _find_holidays(self):
        '''Using Pandas calendar, find all 10 US Federal Holidays,
        plus California's Cesar Chavez day'''
        yr = str(self.base_year)
        cal = USFederalHolidayCalendar()
        holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()

        return [d.strftime('%m-%d') for d in holidays] + ['03-31']

    def _read_link_file(self, file_path, area):
        """ Read the ITN activity data from a single Link file
        File format:
         ANODE         X         Y     BNODE         X         Y  DISTANCE     SPEED    volumes * 26
            19     60729    200387      7010     60671    200259     13992      5000    9.91898    ...
        """
        lcc = Proj(proj='lcc', lat_1=30.0, lat_2=60, lat_0=37, lon_0=-120.5, rsphere=6370000.00)

        # create dictionary of surrogates and TAZ centroid locations
        surrs = dict([(i, {'vmt': SpatialSurrogate()}) for i in range(26)])
        nodes = {}

        # read ITN link file
        f = open(file_path, 'r')
        for line in f.xreadlines():
            if len(line) < 2:
                continue
            # node names
            anode = int(line[:10])
            bnode = int(line[30: 40])
            # coordinates of nodes
            try:
                x1 = int(line[10: 20])
                y1 = int(line[20: 30])
                lon1, lat1 = lcc(x1, y1, inverse=True)
                gridx1, gridy1 = self._find_grid_cell((lon1, lat1), area)
                nodes[anode] = (gridx1, gridy1)
                x2 = int(line[40: 50])
                y2 = int(line[50: 60])
                lon2, lat2 = lcc(x2, y2, inverse=True)
                gridx2, gridy2 = self._find_grid_cell((lon2, lat2), area)
            except:
                continue
            nodes[bnode] = (gridx2, gridy2)
            # determine how to split amoung different grid cells
            grid_cells = [(gridx1, gridy1)]  # lon / lat
            num_cells = 1.0
            if gridx1 != gridx2 or gridy1 != gridy2:
                num_cells = abs(gridx1 - gridx2) + abs(gridy1 - gridy2)
                if num_cells > 8:
                    num_cells = 8
                elif num_cells == 1:
                    num_cells = 2
                step_lat = (lat2 - lat1) / (num_cells - 1.0)
                step_lon = (lon2 - lon1) / (num_cells - 1.0)
                for step in xrange(1, num_cells):
                    grid_cell = self._find_grid_cell((lon1 + step * step_lon,
                                                      lat1 + step * step_lat), area)
                    grid_cells.append(grid_cell)

            # distance (cm)
            distance = int(line[60: 70])  # TODO: Units???
            # speed (miles/hour * 100)
            # speed = int(line[70: 80])
            # volumes
            for c in xrange(26):
                col = 80 + c * 11
                vol = float(line[col: col + 11].strip())
                if vol <= 0.0:
                    continue
                net_vol = vol / num_cells
                net_vmt = net_vol * distance
                for gc in grid_cells:
                    surrs[c]['vmt'][gc] += net_vmt

        f.close()
        return surrs, nodes

    def _read_taz_file(self, file_path, nodes):
        """ Read the ITN activity data from a single TAZ file
        File format:
          NODE      TIME  DISTANCE     SPEED      IZVOL       ORIG       DEST ... (vol,orig,dest)*3*26
        354067         6    640525      3665    0.00000  375.45021  375.17667 ... (vol,orig,dest)*3*26
        """
        # create dictionary of surrogates
        surrs = dict([(i, {'trips': SpatialSurrogate()}) for i in range(26)])

        # read ITN taz file
        f = open(file_path, 'r')
        for line in f.xreadlines():
            if len(line) < 2:
                continue
            node = int(line[:10])
            grid_cell = nodes[node]
            # time = int(line[10:20])
            # distance = int(line[20:30])
            # speed = int(line[30:40])
            for c in xrange(26):
                col = 40 + c * 33
                trips = float(line[col: col + 11].strip())
                surrs[c]['trips'][grid_cell] += trips

        f.close()
        return surrs

    def _read_grid_corners_file(self):
        ''' Read the NetCDF-formatted, CMAQ-ready grid definition file "DOT file" to read
            the corners of each grid cell.
            The results should be of dimensions one more than the grid dimensions.
        '''
        # read in gridded lat/lon
        data = Dataset(self.grid_file_path, 'r')
        lat_dot = data.variables['LATD'][0][0]
        lon_dot = data.variables['LOND'][0][0]
        data.close()

        # validate dimensions
        if (lat_dot.shape[0] != self.ncols + 1) or (lon_dot.shape[0] != self.ncols + 1):
            raise ValueError('The grid file has the wrong number of cols: ' + self.grid_file_path)
        elif (lat_dot.shape[1] != self.nrows + 1) or (lon_dot.shape[1] != self.nrows + 1):
            raise ValueError('The grid file has the wrong number of rows: ' + self.grid_file_path)

        return lat_dot, lon_dot

    def _find_grid_cell(self, p, county):
        ''' Find the grid cell location of a single point in our 3D grid.
            (Point given as a tuple (height in meters, lon in degrees, lat in degrees)
        '''
        p1 = p[0]  # lon
        p2 = p[1]  # lat

        # find the grid cell bounding box for the county in question
        lat_range = self.county_boxes[county]['lat']
        lon_range = self.county_boxes[county]['lon']

        # loop through all grid cells until you find the correct one
        for i in lat_range:
            for j in lon_range:
                # first, determine if it's even worth continuing East at this Latitude
                min_lon = min(self.lon_dot[i, j], self.lon_dot[i + 1, j])
                if p1 < min_lon:
                    break
                # if so, get the lat/lon max/min for this grid cell
                max_lon = max(self.lon_dot[i, j + 1], self.lon_dot[i + 1, j + 1])
                # test if your point lays within this grid cell
                if p1 <= max_lon and p1 >= min_lon:
                    min_lat = min(self.lat_dot[i, j], self.lat_dot[i, j + 1])
                    max_lat = max(self.lat_dot[i + 1, j], self.lat_dot[i + 1, j + 1])
                    if p2 >= min_lat and p2 <= max_lat:
                        return (i, j)

        # If the grid cells are not found, the ITN files or the bounding boxes need fixing.
        for i in xrange(18, 280):
            for j in xrange(88, 318):
                min_lon = min(self.lon_dot[i, j], self.lon_dot[i + 1, j])
                if p1 < min_lon:
                    break
                max_lon = max(self.lon_dot[i, j + 1], self.lon_dot[i + 1, j + 1])
                if p1 <= max_lon and p1 >= min_lon:
                    min_lat = min(self.lat_dot[i, j], self.lat_dot[i, j + 1])
                    max_lat = max(self.lat_dot[i + 1, j], self.lat_dot[i + 1, j + 1])
                    if p2 >= min_lat and p2 <= max_lat:
                        print('Found lat/lon outside County Bounding Box', county, p, i, j)
                        return (i, j)

        # This should never happen. Unless the Lat/Lon are way outside California.
        exit('ERROR: Lat/Lon not found: ' + str(p))


class Dtim4SpatialData(object):
    """ This class is designed as a helper to make organizing the huge amount of spatial
        information we pull out of the DTIM4 Link/TAZ files easier.
        It is just a multiply-embedded dictionary with keys for things that we find in each file:
        county, date, hour-of-the-day, vehicle type, and activity (VMT, Trips, etc).
    """

    def __init__(self):
        self.data = {}

    def get(self, county, date, hr, veh, act):
        """ Getter method for DTIM 4 Data dictionary """
        return self.data.get(county, {}).get(date, {}).get(hr, {}).get(veh, {}).get(act, None)

    def set(self, county, date, hr, veh, act, surrogate):
        """ Setter method for DTIM 4 Data dictionary """
        # type validation
        if type(surrogate) != SpatialSurrogate:
            raise TypeError('Only spatial surrogates can be used in Dtim4SpatialData.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if county not in self.data:
            self.data[county] = {}
        if date not in self.data[county]:
            self.data[county][date] = {}
        if hr not in self.data[county][date]:
            self.data[county][date][hr] = {}
        if veh not in self.data[county][date][hr]:
            self.data[county][date][hr][veh] = {}

        # add surrogate
        self.data[county][date][hr][veh][act] = surrogate

    def add_file(self, county, date, hr, surrogate_dict):
        """ Setter method to add an entire dictionary of spatial surrogates to this object.
            The dict represents an entire DTIM Link or TAZ file. So it has two layers of keys:
            vehicle type and activity type, then it has a spatial surrogate
        """
        for veh in surrogate_dict:
            for act in surrogate_dict[veh]:
                self.set(county, date, hr, veh, act, surrogate_dict[veh][act])

    def generate_temporal_surrogates(self):
        """ Use the data in these spatial surrogates to create a temporal surrogate """
        t = Dtim4Temporal()

        for county, county_data in self.data.iteritems():
            for date, date_data in county_data.iteritems():
                for hr, hr_data in date_data.iteritems():
                    for veh, veh_data in hr_data.iteritems():
                        for act in veh_data:
                            total = sum(veh_data[act].values())
                            t.set_at_hour(county, data, veh, act, int(hr), total)

        return t

    def surrogates(self):
        """ Finally, normalize all the spatial surrogates, so the grid cells sum to 1.0. """
        for county in self.data:
            for date in self.data[county]:
                for hr in self.data[county][date]:
                    for veh in self.data[county][date][hr]:
                        for act in self.data[county][date][hr][veh]:
                            self.data[county][date][hr][veh][act] = self.data[county][date][hr][veh][act].surrogate()


class Dtim4TemporalData(object):
    """ This class is designed as a helper to make organizing the huge amount of temporal
        information we pull out of the DTIM4 Link/TAZ files easier.
        It is just a multiply-embedded dictionary with keys for things that we find in each file:
        county, date, hour-of-the-day, vehicle type, and activity (VMT, Trips, etc).
    """

    def __init__(self):
        self.data = {}

    def get(self, county, date, veh, act):
        """ Getter method for DTIM 4 Data dictionary """
        return self.data.get(county, {}).get(date, {}).get(veh, {}).get(act, None)

    def set(self, county, date, veh, act, surrogate):
        """ Setter method for DTIM 4 Data dictionary """
        # type validation
        if type(surrogate) != TemporalSurrogate:
            raise TypeError('Only temporal surrogates can be used in Dtim4TemporalData.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if county not in self.data:
            self.data[county] = {}
        if date not in self.data[county]:
            self.data[county][date] = {}
        if veh not in self.data[county][date]:
            self.data[county][date][veh] = {}

        # add surrogate
        self.data[county][date][veh][act] = surrogate

    def set_at_hour(self, county, date, veh, act, hr, value):
        """ Setter method for DTIM 4 Data dictionary """
        # auto-fill the mulit-level dictionary format, to hide this from the user
        if county not in self.data:
            self.data[county] = {}
        if date not in self.data[county]:
            self.data[county][date] = {}
        if veh not in self.data[county][date]:
            self.data[county][date][veh] = {}
        if act not in self.data[county][date][veh]:
            self.data[county][date][veh][act] = TemporalSurrogate()

        # add surrogate
        self.data[county][date][veh][act][hr - 1] += value

    def add_file(self, county, date, hr, surrogate_dict):
        """ Setter method to add an entire dictionary of temporal surrogates to this object.
            The dict represents an entire DTIM Link or TAZ file. So it has two layers of keys:
            vehicle type and activity type, then it has a temporal surrogate
        """
        for veh in surrogate_dict:
            for act in surrogate_dict[veh]:
                self.set_at_hour(county, date, veh, act, hr, surrogate_dict[veh][act])

    def surrogates(self):
        """ Finally, normalize all the temporal surrogates, so the 24 hours sum to 1.0. """
        for county in self.data:
            for date in self.data[county]:
                for veh in self.data[county][date]:
                    for act in self.data[county][date][veh]:
                        self.data[county][date][veh][act] = self.data[county][date][veh][act].surrogate()
