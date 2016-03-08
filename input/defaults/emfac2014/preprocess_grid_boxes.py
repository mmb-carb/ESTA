
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
# CA State 12km Grid
'''
GRIDCRO2D = 'GRIDCRO2D.California_12km_97x107'
ROWS = 97
COLS = 107
'''
# SCAQMD 4km Grid
'''
GRIDCRO2D = 'GRIDCRO2D.SCAQMD_4km_102x156'
ROWS = 102
COLS = 156
'''

# TODO: read CSV, output file path

def main():
    # pull global config variables
    gridcro2d = GRIDCRO2D
    rows = ROWS
    cols = COLS
    region_boxes_lat_lon = CA_COUNTY_BOXES_LAT_LON

    # parse command line
    a = 1
    while a < len(sys.argv):
        if sys.argv[a] == '-gridcro2d':
            gridcro2d = sys.argv[a + 1]
        elif sys.argv[a] == '-rows':
            rows = int(sys.argv[a + 1])
        elif sys.argv[a] == '-cols':
            cols = int(sys.argv[a + 1])
        else:
            usage()
        a += 2

    # print bounding boxes
    pcb = PreprocessRegionBoxes(gridcro2d, rows, cols, region_boxes_lat_lon)
    boxes = pcb.find_all_region_boxes()
    pprint(boxes)


def usage():
    print('\n\n\t\tPREPROCESS GRIG REGIONAL BOXES\n\n')
    print('This script can either be run using global config variables, or by setting')
    print('the three command line flags:\n')
    print('\t-gridcro2d - path to the CMAQ-ready GRID CROSS 2D file')
    print('\t-rows - number of rows in the above domain')
    print('\t-cols - number of columns in the above domain\n')
    print('Example usages:\n')
    print('\tpython preprocess_grid_boxes.py')
    print('\tpython preprocess_grid_boxes.py -gridcro2d GRIDCRO2D.California_12km_97x107 ' +
          '-rows 97 -cols 107\n\n')
    exit()


class PreprocessRegionBoxes(object):

    def __init__(self, grid_file_path, nrows, ncols, region_lat_lon_boxes):
        self.grid_file_path = grid_file_path
        self.nrows = nrows
        self.ncols = ncols
        self.region_lat_lon_boxes = region_lat_lon_boxes
        self.lat_dot, self.lon_dot = self._read_grid_corners_file()
        self.rad_factor = pi / 180.0  # need angles in radians
        self.kdtree = {}
        self._create_kdtree()

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


# California County bounding boxes:  [min lat, min lon, max lat, max lon]
CA_COUNTY_BOXES_LAT_LON = {1: [37.44, -122.38, 37.91, -121.46],   # Alameda
                           2: [38.31, -120.18, 38.94, -119.50],   # Alpine
                           3: [38.20, -121.03, 38.71, -120.00],   # Amador
                           4: [39.28, -122.10, 40.16, -121.00],   # Butte
                           5: [37.82, -121.00, 38.52, -120.00],   # Calaveras
                           6: [38.91, -122.79, 39.42, -121.79],   # Colusa
                           7: [37.71, -122.45, 38.10, -121.53],   # Contra_Costa
                           8: [41.35, -124.61, 42.10, -123.50],   # Del_Norte
                           9: [38.50, -121.15, 39.07, -119.87],   # El_Dorado
                           10: [35.90, -120.92, 37.59, -118.35],  # Fresno
                           11: [39.37, -122.94, 39.80, -121.84],  # Glenn
                           12: [39.89, -124.61, 41.49, -123.40],  # Humboldt
                           13: [32.51, -116.11, 33.49, -114.45],  # Imperial
                           14: [35.77, -118.80, 37.47, -115.63],  # Inyo
                           15: [34.78, -120.20, 35.80, -117.61],  # Kern
                           16: [35.77, -120.32, 36.49, -119.47],  # Kings
                           17: [38.66, -123.10, 39.59, -122.34],  # Lake
                           18: [39.70, -121.34, 41.22, -119.90],  # Lassen
                           19: [33.67, -118.98, 34.88, -117.60],  # Los_Angeles
                           20: [36.76, -120.55, 37.78, -119.02],  # Madera
                           21: [37.79, -123.06, 38.37, -122.44],  # Marin
                           22: [37.19, -120.40, 37.91, -119.30],  # Mariposa
                           23: [38.67, -123.99, 40.09, -122.82],  # Mendocino
                           24: [36.74, -121.25, 37.64, -120.05],  # Merced
                           25: [41.15, -121.47, 42.05, -119.93],  # Modoc
                           26: [37.46, -119.66, 38.72, -117.83],  # Mono
                           27: [35.74, -122.16, 36.99, -120.15],  # Monterey
                           28: [38.15, -122.65, 38.87, -122.06],  # Napa
                           29: [39.00, -121.28, 39.53, -120.00],  # Nevada
                           30: [33.35, -118.14, 33.95, -117.40],  # Orange
                           31: [38.71, -121.49, 39.32, -120.00],  # Placer
                           32: [39.59, -121.50, 40.45, -120.09],  # Plumas
                           33: [33.42, -117.68, 34.08, -114.43],  # Riverside
                           34: [38.00, -121.87, 38.74, -121.02],  # Sacramento
                           35: [36.19, -121.65, 36.99, -120.59],  # San_Benito
                           36: [33.86, -117.81, 35.81, -114.13],  # San_Bernardino
                           37: [32.50, -117.70, 33.51, -115.98],  # San_Diego
                           38: [37.69, -122.53, 37.83, -122.35],  # San_Francisco
                           39: [37.48, -121.59, 38.31, -120.92],  # San_Joaquin
                           40: [34.89, -121.64, 35.80, -119.37],  # San_Luis_Obispo
                           41: [36.97, -122.70, 37.83, -122.08],  # San_Mateo
                           42: [33.70, -121.15, 35.12, -118.96],  # Santa_Barbara
                           43: [36.89, -122.21, 37.49, -121.20],  # Santa_Clara
                           44: [36.79, -122.35, 37.29, -121.58],  # Santa_Cruz
                           45: [40.28, -123.07, 41.19, -121.31],  # Shasta
                           46: [39.39, -121.06, 39.78, -120.00],  # Sierra
                           47: [40.99, -123.72, 42.01, -121.44],  # Siskiyou
                           48: [38.03, -122.41, 38.54, -121.59],  # Solano
                           49: [38.07, -123.65, 38.86, -122.34],  # Sonoma
                           50: [37.13, -121.49, 38.08, -120.38],  # Stanislaus
                           51: [38.73, -121.95, 39.31, -121.41],  # Sutter
                           52: [39.79, -123.07, 40.46, -121.34],  # Tehama
                           53: [39.97, -123.63, 41.37, -122.44],  # Trinity
                           54: [35.78, -119.58, 36.75, -117.98],  # Tulare
                           55: [37.63, -120.66, 38.44, -119.19],  # Tuolumne
                           56: [33.97, -119.50, 34.91, -118.58],  # Ventura
                           57: [38.31, -122.43, 38.93, -121.50],  # Yolo
                           58: [38.91, -121.64, 39.64, -121.00]}  # Yuba


# US State bounding boxes:  [min lat, min lon, max lat, max lon]
US_STATE_BOXES = {1: [30.2198, -88.4711, 35.0012, -84.8892],     # Alabama
                  2: [51.2184, 172.4613, 71.3516, -129.9863],    # Alaska
                  4: [31.3316, -114.8152, 37.0003, -109.0425],   # Arizona
                  5: [33.0021, -94.6162, 36.5019, -89.6432],     # Arkansas
                  6: [32.5366, -124.4108, 42.0062, -114.1361],   # California
                  8: [36.9948, -109.048, 41.0039, -102.043],     # Colorado
                  9: [40.9875, -73.7272, 42.05, -71.7993],       # Connecticut
                  10: [38.4517, -75.7865, 39.8318, -75.0471],    # Delaware
                  11: [38.7912, -77.1174, 38.9939, -76.9093],    # District of Columbia
                  12: [24.5457, -87.6331, 31.003, -80.0312],     # Florida
                  13: [30.3567, -85.6067, 35.0012, -80.8417],    # Georgia
                  15: [18.9209, -160.23, 22.229, -154.8078],     # Hawaii
                  16: [41.9952, -117.2415, 49.0002, -111.0471],  # Idaho
                  17: [36.9729, -91.5108, 42.5101, -87.4962],    # Illinois
                  18: [37.7725, -88.0603, 41.7597, -84.7851],    # Indiana
                  19: [40.3795, -96.6372, 43.5014, -90.1635],    # Iowa
                  20: [36.9948, -102.0539, 40.0016, -94.5943],   # Kansas
                  21: [36.4964, -89.572, 39.1472, -81.97],       # Kentucky
                  22: [28.9273, -94.0412, 33.0185, -88.8162],    # Louisiana
                  23: [43.0578, -71.0818, 47.4612, -66.9522],    # Maine
                  24: [37.9149, -79.4889, 39.7223, -75.0471],    # Maryland
                  25: [41.2449, -73.5081, 42.888, -69.9262],     # Massachusetts
                  26: [41.694, -90.4154, 48.1897, -82.4136],     # Michigan
                  27: [43.5014, -97.2287, 49.3836, -89.4898],    # Minnesota
                  28: [30.176, -91.6532, 34.9957, -88.0987],     # Mississippi
                  29: [35.998, -95.7664, 40.615, -89.101],       # Missouri
                  30: [44.3613, -116.0475, 49.0002, -104.0475],  # Montana
                  31: [40.0016, -104.053, 43.003, -95.3063],     # Nebraska
                  32: [35.0012, -120.0019, 42.0007, -114.0429],  # Nevada
                  33: [42.6963, -72.5551, 45.3033, -70.7039],    # New Hampshire
                  34: [38.9336, -75.562, 41.3599, -73.8915],     # New Jersey
                  35: [31.3316, -109.048, 37.0003, -103.0014],   # New Mexico
                  36: [40.4946, -79.7628, 45.0185, -71.8541],    # New York
                  37: [33.8455, -84.3196, 36.5895, -75.4579],    # North Carolina
                  38: [45.9332, -104.0475, 49.0002, -96.5606],   # North Dakota
                  39: [38.4243, -84.818, 41.9788, -80.5186],     # Ohio
                  40: [33.6374, -103.0014, 37.0003, -94.43],     # Oklahoma
                  41: [41.9952, -124.5532, 46.2672, -116.4638],  # Oregon
                  42: [39.7223, -80.5186, 42.2691, -74.6966],    # Pennsylvania
                  72: [17.9296, -67.9381, 18.5156, -65.2598],    # Puerto Rico
                  44: [41.1518, -71.8596, 42.0171, -71.1202],    # Rhode Island
                  45: [32.0327, -83.3392, 35.2148, -78.5414],    # South Carolina
                  46: [42.4882, -104.0585, 45.9441, -96.4346],   # South Dakota
                  47: [34.9847, -90.3114, 36.6771, -81.6468],    # Tennessee
                  48: [25.8383, -106.6381, 36.5019, -93.5154],   # Texas
                  49: [37.0003, -114.0484, 42.0007, -109.0425],  # Utah
                  50: [42.7291, -73.4369, 45.013, -71.4652],     # Vermont
                  51: [36.5512, -83.6733, 39.4649, -75.2443],    # Virginia
                  53: [45.5443, -124.7339, 49.0002, -116.9183],  # Washington
                  54: [37.2029, -82.6437, 40.637, -77.7199],     # West Virginia
                  55: [42.4936, -92.8855, 47.0778, -86.8061],    # Wisconsin
                  56: [40.9984, -111.0525, 45.0021, -104.053]}   # Wyoming


if __name__ == '__main__':
    main()
