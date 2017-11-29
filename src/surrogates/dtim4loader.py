
from netCDF4 import Dataset
import os
from pyproj import Proj
import sys
import numpy as np
from math import pi
from numpy import cos, sin
from scipy.spatial import cKDTree
from src.core.spatial_loader import SpatialLoader
from spatial_surrogate import SpatialSurrogate
from spatial_surrogate_data import SpatialSurrogateData


class Dtim4Loader(SpatialLoader):
    """ This class is designed to load the spatial surrogates represtented by the DTIM4 input
        link and TAZ files.
    """

    DEFAULT_DTIM_HOUR = 17
    MAX_STEPS = 12
    RAD_FACTOR = np.float32(pi / 180.0)  # need angles in radians

    def __init__(self, config, position):
        super(Dtim4Loader, self).__init__(config, position)
        self.nrows = self.config.getint('GridInfo', 'rows')
        self.ncols = self.config.getint('GridInfo', 'columns')
        self.grid_file_path = self.config['GridInfo']['grid_cross_file']
        self.lat_dot, self.lon_dot = self._read_grid_corners_file()
        self.data = SpatialSurrogateData()
        self.region_boxes = self.config.eval_file('Surrogates', 'region_boxes')
        self.regions = self.config.parse_regions('Regions', 'regions')
        self.eic_labels = ['vmt', 'trips']
        self.kdtrees = {}
        self._create_kdtrees()

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read DTIM4 road network files """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = SpatialSurrogateData()

        # the current file format requires us to select a specific hour of the day
        hr = Dtim4Loader.DEFAULT_DTIM_HOUR

        # loop through all the regions
        for region in self.regions:
            region_code = '%03d' % region

            # build the file paths
            link_file = os.path.join(self.directory, region_code,
                                     'dtim_link_' + region_code + '_tuth_%02d.dat' % hr)
            index = link_file.rfind('link')
            taz_file = link_file[:index] + 'taz' + link_file[index + 4:]

            # read link file
            if not os.path.exists(link_file):
                sys.exit('Link file does not exist: ' + link_file)
                continue
            link_spatial_surrs, nodes = self._read_link_file(link_file, region)

            # read TAZ file (TAZ file needs node definitions from link file)
            if not os.path.exists(taz_file):
                sys.exit('TAZ file does not exist: ' + taz_file)
            taz_spatial_surrs = self._read_taz_file(taz_file, nodes)

            # add surrogate data to the correct regions
            spatial_surrogates.add_file(region, link_spatial_surrs)
            spatial_surrogates.add_file(region, taz_spatial_surrs)

        # normalize surrogates
        spatial_surrogates.surrogates()

        return spatial_surrogates, temporal_surrogates

    def _read_link_file(self, file_path, area):
        """ Read the DTIM activity data from a single Link file
        File format:
         ANODE         X         Y     BNODE         X         Y  DISTANCE     SPEED    volumes * 26
            19     60729    200387      7010     60671    200259     13992      5000    9.91898  ...
        """
        zero = np.float32(0.0)
        one = np.float32(1.0)
        lcc = Proj(proj='lcc', lat_1=30.0, lat_2=60, lat_0=37, lon_0=-120.5, rsphere=6370000.00,
                   ellps='sphere')

        # create dictionary of surrogates and TAZ centroid locations
        surrs = dict([(i, {self.eic_labels[0]: SpatialSurrogate()}) for i in range(26)])
        nodes = {}

        # read DTIM link file
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
                # NOTE: This is a bare exception because QAing DTIM link files is a complex task
                continue
            nodes[bnode] = (gridx2, gridy2)
            # determine how to split amoung different grid cells
            grid_cells = [(gridx1, gridy1)]  # lon / lat
            num_cells = one
            if gridx1 != gridx2 or gridy1 != gridy2:
                num_cells = abs(gridx1 - gridx2) + abs(gridy1 - gridy2)
                if num_cells > Dtim4Loader.MAX_STEPS:
                    num_cells = Dtim4Loader.MAX_STEPS
                elif num_cells == 1:
                    num_cells = 2
                step_lat = (lat2 - lat1) / (num_cells - one)
                step_lon = (lon2 - lon1) / (num_cells - one)
                for step in xrange(1, num_cells):
                    grid_cell = self._find_grid_cell((lon1 + step * step_lon,
                                                      lat1 + step * step_lat), area)
                    grid_cells.append(grid_cell)

            # distance (cm)
            distance = int(line[60: 70])  # units currently don't matter
            # speed (miles/hour * 100)
            # speed = int(line[70: 80])
            # volumes
            for c in xrange(26):
                col = 80 + c * 11
                vol = np.float32(line[col: col + 11].strip())
                if vol <= zero:
                    continue
                net_vol = vol / num_cells
                net_vmt = np.float32(net_vol * distance)
                for gc in grid_cells:
                    surrs[c][self.eic_labels[0]][gc] += net_vmt

        f.close()
        return surrs, nodes

    def _read_taz_file(self, file_path, nodes):
        """ Read the DTIM activity data from a single TAZ file
        File format:
          NODE      TIME  DISTANCE     SPEED      IZVOL       ORIG       DEST ... (vol,orig,dest)*3*26
        354067         6    640525      3665    0.00000  375.45021  375.17667 ... (vol,orig,dest)*3*26
        """
        # create dictionary of surrogates
        surrs = dict([(i, {self.eic_labels[1]: SpatialSurrogate()}) for i in xrange(26)])

        # read DTIM taz file
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
                trips = np.float32(line[col: col + 11].strip())
                surrs[c][self.eic_labels[1]][grid_cell] += trips

        f.close()
        return surrs

    def _read_grid_corners_file(self):
        ''' Read the NetCDF-formatted, CMAQ-ready grid definition file "DOT file" to read
            the corners of each grid cell.
            The results should be of dimensions one more than the grid dimensions.
        '''
        # read in gridded lat/lon
        data = Dataset(self.grid_file_path, 'r')
        lat_dot = data.variables['LAT'][0][0]
        lon_dot = data.variables['LON'][0][0]
        data.close()

        # validate dimensions
        if (lat_dot.shape[1] != self.ncols) or (lon_dot.shape[1] != self.ncols):
            raise ValueError('The grid file has the wrong number of cols: ' + self.grid_file_path)
        elif (lat_dot.shape[0] != self.nrows) or (lon_dot.shape[0] != self.nrows):
            raise ValueError('The grid file has the wrong number of rows: ' + self.grid_file_path)

        return lat_dot, lon_dot

    def _create_kdtrees(self):
        """ Create a KD Tree for each region """
        lat_vals = self.lat_dot[:] * self.RAD_FACTOR
        lon_vals = self.lon_dot[:] * self.RAD_FACTOR

        for region in self.regions:
            # find the grid cell bounding box for the region in question
            lat_min, lat_max = self.region_boxes[region]['lat']
            lon_min, lon_max = self.region_boxes[region]['lon']

            # slice grid down to this region
            latvals = lat_vals[lat_min:lat_max, lon_min:lon_max]
            lonvals = lon_vals[lat_min:lat_max, lon_min:lon_max]

            # create tree
            clat,clon = cos(latvals),cos(lonvals)
            slat,slon = sin(latvals),sin(lonvals)
            triples = list(zip(np.ravel(clat*clon), np.ravel(clat*slon), np.ravel(slat)))
            self.kdtrees[region] = cKDTree(triples)

    def _find_grid_cell(self, p, region):
        ''' Find the grid cell location of a single point in our 3D grid.
            (Point given as a tuple (height in meters, lon in degrees, lat in degrees)
        '''
        lat_min, lat_max = self.region_boxes[region]['lat']
        lon_min, lon_max = self.region_boxes[region]['lon']

        # define parameters
        lon0 = p[0] * self.RAD_FACTOR
        lat0 = p[1] * self.RAD_FACTOR

        # run KD Tree algorithm
        clat0,clon0 = cos(lat0),cos(lon0)
        slat0,slon0 = sin(lat0),sin(lon0)
        dist_sq_min, minindex_1d = self.kdtrees[region].query([clat0*clon0, clat0*slon0, slat0])
        y, x = np.unravel_index(minindex_1d, (lat_max - lat_min, lon_max - lon_min))

        return lat_min + y + 1, lon_min + x + 1
