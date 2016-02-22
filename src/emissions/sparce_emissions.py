
from collections import defaultdict


class SparceEmissions(defaultdict):
    """ This is a sparce-grid representation of emissions on a grid.
        For every n-tuple representing a spot on the grid, there is a dictionary
        representing the pollutant and emissions on that grid.
        This grid represents all the emissions for a single EIC during a single hour.
    """

    def __init__(self):
        defaultdict.__init__(self, lambda: defaultdict(float))

    def __getitem__(self, key):
        """ Setter method for sparce-grid emissions """
        val = defaultdict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """ Getter method for sparce-grid emissions """
        if type(val) != defaultdict:
            raise TypeError('The sparce-grid emissions must be two levels deep: EIC and pollutant.')
        for value in val.itervalues():
            if type(value) != float:
                raise TypeError('Emissions values must be of type float.')
        defaultdict.__setitem__(self, key, val)

    def scale(self, factor):
        """ Scale all of the emissions in this grid by the given factor """
        for single_cell in defaultdict.itervalues(self):
            for poll in single_cell.iterkeys():
                single_cell[poll] *= factor

    def add_grid(self, grid):
        """ add a different sparce grid of emissions to this one """
        for cell, cell_data in grid.iteritems():
            if not defaultdict.__contains__(self, cell):
                defaultdict.__setitem__(self, cell, cell_data)
            else:
                for poll, value in cell_data.iteritems():
                    cell_dict = defaultdict.__getitem__(self, cell)
                    cell_dict[poll] += value

    def __repr__(self):
        return defaultdict.__repr__(self).replace('defaultdict', self.__class__.__name__, 1)
