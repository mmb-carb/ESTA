
import numpy as np
from math import pi
from netCDF4 import Dataset
from numpy import cos, sin
from pprint import pprint
from scipy.spatial import cKDTree
import sys

# CONFIGURABLES
# CA State 4km Grid
GRIDCRO2D = 'GRIDCRO2D.California_4km_291x321'
ROWS = 291
COLS = 321
REGIONS_FILE = 'california_counties_lat_lon_bounding_boxes.csv'
# CA State 12km Grid
'''
GRIDCRO2D = 'GRIDCRO2D.California_12km_97x107'
ROWS = 97
COLS = 107
REGIONS_FILE = 'california_counties_lat_lon_bounding_boxes.csv'
'''
# SCAQMD 4km Grid
'''
GRIDCRO2D = 'GRIDCRO2D.SCAQMD_4km_102x156'
ROWS = 102
COLS = 156
REGIONS_FILE = 'california_counties_lat_lon_bounding_boxes.csv'
'''


def main():
    # pull global config variables
    gridcro2d = GRIDCRO2D
    rows = ROWS
    cols = COLS
    regions_file = REGIONS_FILE

    # parse command line
    a = 1
    while a < len(sys.argv):
        if sys.argv[a] == '-gridcro2d':
            gridcro2d = sys.argv[a + 1]
        elif sys.argv[a] == '-rows':
            rows = int(sys.argv[a + 1])
        elif sys.argv[a] == '-cols':
            cols = int(sys.argv[a + 1])
        elif sys.argv[a] == '-regions':
            regions_file = int(sys.argv[a + 1])
        else:
            usage()
        a += 2

    # print bounding boxes
    pcb = PreprocessRegionBoxes(gridcro2d, rows, cols, regions_file)
    boxes = pcb.find_all_region_boxes()
    pprint(boxes)


def usage():
    print('\n\n\t\tPREPROCESS GRIG REGIONAL BOXES\n\n')
    print('This script can either be run using global config variables, or by setting')
    print('the three command line flags:\n')
    print('\t-gridcro2d - path to the CMAQ-ready GRID CROSS 2D file')
    print('\t-rows - number of rows in the above domain')
    print('\t-cols - number of columns in the above domain\n')
    print('\t-regions - path to CSV file of lat/lon bounding boxes for your regions\n')
    print('Example usages:\n')
    print('\tpython preprocess_grid_boxes.py')
    print('\tpython preprocess_grid_boxes.py -gridcro2d GRIDCRO2D.California_12km_97x107 ' +
          '-rows 97 -cols 107 -regions california_counties_lat_lon_bounding_boxes.csv\n')
    print('\nThe Regions CSV file needs to have the following format:\n')
    print('\tregion_code,region_descriptor,min_lat,min_lon,max_lat,max_lon')
    print('\t1,Alameda,37.44,-122.38,37.91,-121.46')
    print('\t2,Alpine,38.31,-120.18,38.94,-119.50\n\n')
    exit()


class PreprocessRegionBoxes(object):

    def __init__(self, grid_file_path, nrows, ncols, regions_file):
        self.grid_file_path = grid_file_path
        self.nrows = nrows
        self.ncols = ncols
        self.regions_file = regions_file
        self.region_lat_lon_boxes = None
        self.lat_dot, self.lon_dot = self._read_grid_corners_file()
        self.rad_factor = pi / 180.0  # need angles in radians
        self.kdtree = {}
        self._create_kdtree()
        self._read_regions_file()

    def _read_regions_file(self):
        ''' Read the regions lat/lon bounding boxes CSV file.
            It has the format:

            region_code,region_descriptor,min_lat,min_lon,max_lat,max_lon
            1,Alameda,37.44,-122.38,37.91,-121.46
            2,Alpine,38.31,-120.18,38.94,-119.50
        '''
        # reset bounding boxes, just in case
        self.region_lat_lon_boxes = {}

        # open CSV and drop header
        f = open(self.regions_file, 'r')
        header = f.readline()

        # iterate through the data lines
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) != 6:
                continue
            region = int(ln[0])
            box = [float(v) for v in ln[2:]]
            self.region_lat_lon_boxes[region] = box

        f.close()

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

    def _create_kdtree(self):
        """ Create a KD Tree for the domain """
        # convert to radians
        latvals = self.lat_dot[:] * self.rad_factor
        lonvals = self.lon_dot[:] * self.rad_factor

        # create tree
        clat,clon = cos(latvals),cos(lonvals)
        slat,slon = sin(latvals),sin(lonvals)
        triples = list(zip(np.ravel(clat*clon), np.ravel(clat*slon), np.ravel(slat)))
        self.kdtree = cKDTree(triples)

    def find_grid_cell(self, p):
        ''' Find the grid cell location of a single point in our 3D grid.
            Point given as a tuple (height in meters, lon in degrees, lat in degrees).
        '''
        # convert to radians
        lon0 = p[0] * self.rad_factor
        lat0 = p[1] * self.rad_factor

        # run KD Tree algorithm
        clat0,clon0 = cos(lat0),cos(lon0)
        slat0,slon0 = sin(lat0),sin(lon0)
        dist_sq_min, minindex_1d = self.kdtree.query([clat0 * clon0, clat0 * slon0, slat0])
        y, x = np.unravel_index(minindex_1d, (self.nrows, self.ncols))

        return y + 1, x + 1

    def find_all_region_boxes(self):
        ''' master method to return a dictionary containing the bounding
            boxes for each region, in your chosen grid.
        '''
        boxes = {}

        for region in self.region_lat_lon_boxes:
            ll_lat, ll_lon, ur_lat, ur_lon = self.region_lat_lon_boxes[region]
            ll_y, ll_x = self.find_grid_cell((ll_lon, ll_lat))
            ur_y, ur_x = self.find_grid_cell((ur_lon, ur_lat))
            boxes[region] = {'lon': (ll_x - 1, ur_x + 1), 'lat': (ll_y - 1, ur_y + 1)}

        return boxes


if __name__ == '__main__':
    main()
