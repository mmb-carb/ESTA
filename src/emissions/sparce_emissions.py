
#from scipy.sparse import lil_matrix  # TODO: Also try dok_matrix, or others...
#from scipy.sparse import dok_matrix
from collections import defaultdict
from functools import partial
import numpy as np


# TODO: "sparse" is spelled wrong...  d'oh.
class SparceEmissions(defaultdict):
    """ This is a sparce-grid representation of emissions on a grid.
        For every n-tuple representing a location on the grid, there is a dictionary
        representing the pollutant and emissions on that grid.
        This grid represents all the emissions for a single EIC during a single hour.
    """

    def __init__(self):
        #defaultdict.__init__(self, partial(dok_matrix, (291, 321), dtype=np.float32))  # TODO: hard-coded dimensions
        defaultdict.__init__(self, partial(np.zeros, (291, 321), dtype=np.float32))  # TODO: hard-coded dimensions

    def __getitem__(self, key):
        """ Setter method for sparce-grid emissions """
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        """ Getter method for sparce-grid emissions """
        defaultdict.__setitem__(self, key, val)
        '''
        print(val)  # TODO: Type np.ndarray((291,321))... whoops!
        print(type(val))

        print(key)
        print(type(key))
        '''

    def scale(self, factor):
        """ Scale all of the emissions in this grid by the given factor """
        for grid in defaultdict.itervalues(self):
            grid *= factor

    def add_grid(self, grid):
        """ add a different sparce grid of emissions to this one """
        for poll, grid_data in grid.iteritems():
            if not defaultdict.__contains__(self, poll):  # TODO: What if this were in the opposite order?
                defaultdict.__setitem__(self, poll, grid_data)
            else: 
                this_grid = defaultdict.__getitem__(self, poll)
                this_grid += grid_data

    def __deepcopy__(self, emis):
        """ standard Python helper to allow for deepcopy(x) functionality """
        e = SparceEmissions()

        for poll, grid_data in self.iteritems():
            e[poll] = grid_data.copy()

        return e

    def __repr__(self):
        """ standard Python helper to allower for str(x) and print(x) """
        return self.__class__.__name__ + '(' + \
            str(dict((k, str(v)) for k, v in self.iteritems()))[1: -1] + ')'
