
from collections import defaultdict
from netCDF4 import Dataset
import os
import sys
import numpy as np
from math import pi
from numpy import cos, sin
from scipy.spatial import cKDTree
from src.core.spatial_loader import SpatialLoader
from dtim4loader import Dtim4Loader, SpatialSurrogateData
from spatial_surrogate import SpatialSurrogate
from temporal_surrogate import TemporalSurrogate


class Itn4Loader(Dtim4Loader):
    """ This class is designed to load the spatial surrogates represtented by the ITN4
        road network input link and TAZ files.
    """

    MAX_STEPS = 12

    def __init__(self, config, directory):
        super(Itn4Loader, self).__init__(config, directory)
        self.load_taz = False
        if 'use_taz' in self.config['Surrogates']:
            if self.config['Surrogates']['use_taz'].lower() == 'true':
                self.load_taz = True

    def load(self, spatial_surrogates, temporal_surrogates):
        """ Overriding the abstract loader method to read ITN4 road network files """
        # initialize surroagates, if needed
        if not spatial_surrogates:
            spatial_surrogates = SpatialSurrogateData()

        # loop through all the regions
        for region in self.regions:
            fips = self._county_to_fips(region)
            # build the file paths
            link_file = os.path.join(self.directory, fips,
                                     'esta_link_' + fips + '.dat')
            index = link_file.rfind('link')

            # read link file
            if not os.path.exists(link_file):
                sys.exit('Link file does not exist: ' + link_file)
                continue
            link_spatial_surrs, nodes = self._read_link_file(link_file, region)
            spatial_surrogates.add_file(region, link_spatial_surrs)

            # read TAZ file (TAZ file needs node definitions from link file)
            if self.load_taz:
                taz_file = link_file[:index] + 'taz' + link_file[index + 4:]
                if not os.path.exists(taz_file):
                    sys.exit('TAZ file does not exist: ' + taz_file)
                taz_spatial_surrs = self._read_taz_file(taz_file, nodes)
                spatial_surrogates.add_file(region, taz_spatial_surrs)

        # normalize surrogates
        spatial_surrogates.surrogates()

        return spatial_surrogates, temporal_surrogates

    def _read_link_file(self, file_path, area):
        """ Read the ITN activity data from a single Link file
        File format:
        ANODE,X,Y,BNODE,X,Y,DISTANCE,SPEED,volumes * 26
        3131,-122.191,37.784,3115,-122.188,37.783,313.648,29004425.98  ...
        """
        # create dictionary of surrogates and TAZ centroid locations
        surrs = dict([(i, {'vmt': SpatialSurrogate()}) for i in range(26)])
        nodes = {}

        # read ITN link file
        f = open(file_path, 'r')
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) < 30:
                continue
            # node names
            anode = int(ln[0])
            bnode = int(ln[3])
            # coordinates of nodes
            try:
                lon1 = float(ln[1])
                lat1 = float(ln[2])
                gridx1, gridy1 = self._find_grid_cell((lon1, lat1), area)
                nodes[anode] = (gridx1, gridy1)
                lon2 = float(ln[4])
                lat2 = float(ln[5])
                gridx2, gridy2 = self._find_grid_cell((lon2, lat2), area)
            except:
                continue
            nodes[bnode] = (gridx2, gridy2)
            # determine how to split amoung different grid cells
            grid_cells = [(gridx1, gridy1)]  # lon / lat
            num_cells = 1.0
            if gridx1 != gridx2 or gridy1 != gridy2:
                num_cells = abs(gridx1 - gridx2) + abs(gridy1 - gridy2)
                if num_cells > Itn4Loader.MAX_STEPS:
                    num_cells = Itn4Loader.MAX_STEPS
                elif num_cells == 1:
                    num_cells = 2
                step_lat = (lat2 - lat1) / (num_cells - 1.0)
                step_lon = (lon2 - lon1) / (num_cells - 1.0)
                for step in xrange(1, num_cells):
                    grid_cell = self._find_grid_cell((lon1 + step * step_lon,
                                                      lat1 + step * step_lat), area)
                    grid_cells.append(grid_cell)

            # distance (cm)
            distance = float(ln[6])  # units currently don't matter
            # speed (miles/hour * 100)
            # speed = float(ln[7])
            # volumes
            for col in xrange(26):
                vol = float(ln[8 + col])
                if vol <= 0.0:
                    continue
                net_vmt = (vol / num_cells) * distance
                for gc in grid_cells:
                    surrs[col]['vmt'][gc] += net_vmt

        f.close()
        return surrs, nodes

    def _read_taz_file(self, file_path, nodes):
        """ Read the ITN activity data from a single TAZ file
        File format:
        NODE,TIME,DISTANCE,SPEED,IZVOL,ORIG,DEST,... (vol,orig,dest)*3*26
        354067,6,640525,3665.09,0.00000,375.45021,375.17667,... (vol,orig,dest)*3*26
        """
        # create dictionary of surrogates
        surrs = dict([(i, {'trips': SpatialSurrogate()}) for i in range(26)])

        # read ITN taz file
        f = open(file_path, 'r')
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) < 26:
                continue
            node = int(ln[0])
            grid_cell = nodes[node]
            # time = int(ln[1])
            # distance = int(ln[2])
            # speed = float(ln[3])
            for i in xrange(26):
                trips = float(ln[4 + 3 * i])
                surrs[i]['trips'][grid_cell] += trips

        f.close()
        return surrs
