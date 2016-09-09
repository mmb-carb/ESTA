
from collections import defaultdict


class SparceEmissions(defaultdict):
    """ This is a sparce-grid representation of emissions on a grid.
        For every n-tuple representing a location on the grid, there is a dictionary
        representing the pollutant and emissions on that grid.
        This grid represents all the emissions for a single EIC during a single hour.
    """

    def __init__(self):
        defaultdict.__init__(self, lambda: defaultdict(float))

    def __getitem__(self, key):
        """ Setter method for sparce-grid emissions """
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        """ Getter method for sparce-grid emissions """
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
                cell_dict = defaultdict.__getitem__(self, cell)
                for poll, value in cell_data.iteritems():
                    cell_dict[poll] += value

    def __deepcopy__(self, emis):
        """ standard Python helper to allow for deepcopy(x) functionality """
        e = SparceEmissions()

        for cell, cell_data in self.iteritems():
            for poll, value in cell_data.iteritems():
                e[cell][poll] = value

        return e

    def __repr__(self):
        """ standard Python helper to allower for str(x) and print(x) """
        return self.__class__.__name__ + '(' + \
            str(dict((k, dict(v)) for k, v in self.iteritems()))[1: -1] + ')'
