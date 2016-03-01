
import numpy as np
from math import pi
from netCDF4 import Dataset
from numpy import cos, sin
from pprint import pprint
from scipy.spatial import cKDTree

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


def main():
    pcb = PreprocessCountyBoxes(GRIDCRO2D, ROWS, COLS)
    boxes = pcb.find_all_county_boxes()
    pprint(boxes)


class PreprocessCountyBoxes(object):

    def __init__(self, grid_file_path, nrows, ncols):
        self.grid_file_path = grid_file_path
        self.nrows = nrows
        self.ncols = ncols
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
        """ Create a KD Tree for the state """
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
            (Point given as a tuple (height in meters, lon in degrees, lat in degrees)
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

    def find_all_county_boxes(self):
        ''' master method to return a dictionary containing the bounding
            boxes for each county (or sub-region), in your chosen grid
        '''
        boxes = {}
        for county in xrange(1, 59):
            ll_lat, ll_lon, ur_lat, ur_lon = COUNTY_BOXES_LAT_LON[county]
            ll_y, ll_x = self.find_grid_cell((ll_lon, ll_lat))
            ur_y, ur_x = self.find_grid_cell((ur_lon, ur_lat))
            boxes[county] = {'lon': (ll_x - 1, ur_x + 1), 'lat': (ll_y - 1, ur_y + 1)}

        return boxes


COUNTY_BOXES_LAT_LON = {1: [37.44, -122.38, 37.91, -121.46],
                        2: [38.31, -120.18, 38.94, -119.50],
                        3: [38.20, -121.03, 38.71, -120.00],
                        4: [39.28, -122.10, 40.16, -121.00],
                        5: [37.82, -121.00, 38.52, -120.00],
                        6: [38.91, -122.79, 39.42, -121.79],
                        7: [37.71, -122.45, 38.10, -121.53],
                        8: [41.35, -124.61, 42.10, -123.50],
                        9: [38.50, -121.15, 39.07, -119.87],
                        10: [35.90, -120.92, 37.59, -118.35],
                        11: [39.37, -122.94, 39.80, -121.84],
                        12: [39.89, -124.61, 41.49, -123.40],
                        13: [32.51, -116.11, 33.49, -114.45],
                        14: [35.77, -118.80, 37.47, -115.63],
                        15: [34.78, -120.20, 35.80, -117.61],
                        16: [35.77, -120.32, 36.49, -119.47],
                        17: [38.66, -123.10, 39.59, -122.34],
                        18: [39.70, -121.34, 41.22, -119.90],
                        19: [33.67, -118.98, 34.88, -117.60],
                        20: [36.76, -120.55, 37.78, -119.02],
                        21: [37.79, -123.06, 38.37, -122.44],
                        22: [37.19, -120.40, 37.91, -119.30],
                        23: [38.67, -123.99, 40.09, -122.82],
                        24: [36.74, -121.25, 37.64, -120.05],
                        25: [41.15, -121.47, 42.05, -119.93],
                        26: [37.46, -119.66, 38.72, -117.83],
                        27: [35.74, -122.16, 36.99, -120.15],
                        28: [38.15, -122.65, 38.87, -122.06],
                        29: [39.00, -121.28, 39.53, -120.00],
                        30: [33.35, -118.14, 33.95, -117.40],
                        31: [38.71, -121.49, 39.32, -120.00],
                        32: [39.59, -121.50, 40.45, -120.09],
                        33: [33.42, -117.68, 34.08, -114.43],
                        34: [38.00, -121.87, 38.74, -121.02],
                        35: [36.19, -121.65, 36.99, -120.59],
                        36: [33.86, -117.81, 35.81, -114.13],
                        37: [32.50, -117.70, 33.51, -115.98],
                        38: [37.69, -122.53, 37.83, -122.35],
                        39: [37.48, -121.59, 38.31, -120.92],
                        40: [34.89, -121.64, 35.80, -119.37],
                        41: [36.97, -122.70, 37.83, -122.08],
                        42: [33.70, -121.15, 35.12, -118.96],
                        43: [36.89, -122.21, 37.49, -121.20],
                        44: [36.79, -122.35, 37.29, -121.58],
                        45: [40.28, -123.07, 41.19, -121.31],
                        46: [39.39, -121.06, 39.78, -120.00],
                        47: [40.99, -123.72, 42.01, -121.44],
                        48: [38.03, -122.41, 38.54, -121.59],
                        49: [38.07, -123.65, 38.86, -122.34],
                        50: [37.13, -121.49, 38.08, -120.38],
                        51: [38.73, -121.95, 39.31, -121.41],
                        52: [39.79, -123.07, 40.46, -121.34],
                        53: [39.97, -123.63, 41.37, -122.44],
                        54: [35.78, -119.58, 36.75, -117.98],
                        55: [37.63, -120.66, 38.44, -119.19],
                        56: [33.97, -119.50, 34.91, -118.58],
                        57: [38.31, -122.43, 38.93, -121.50],
                        58: [38.91, -121.64, 39.64, -121.00]}


if __name__ == '__main__':
    main()
