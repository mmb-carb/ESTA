
import numpy as np


class SparseEmissions(object):
    """ This is a sparce-grid representation of emissions on a grid.
        For every pollutant there is a NumPy array representing the
        emissions in each cell of the grid.
        This grid represents all the emissions for a single EIC during a single hour.
    """

    def __init__(self, nrows, ncols):
        self._data = {}
        self.pollutants = set()
        self.nrows = nrows
        self.ncols = ncols

    def get(self, poll, cell):
        """ Getter method for sparse grid emissions """
        return self._data[poll][cell]

    def get_grid(self, poll):
        """ Get a copy of an entire pollutant grid """
        return self._data[poll].copy()

    def mask(self, min_val=0.0):
        """ Build a mask of all the grid cells with non-zero emissions
            for any pollutant.
            Note: This method gives no performance gaurantees.
        """
        polls = list(self.pollutants)
        mask = self._data[polls[0]] > min_val
        for poll in polls[1:]:
            mask += self._data[poll] > min_val

        return mask

    def add_poll(self, poll):
        """ Add a single pollutant
            This is used to help speed up the processing.
        """
        if poll not in self.pollutants:
            self.pollutants.add(poll)
            self._data[poll] = np.zeros((self.nrows, self.ncols), dtype=np.float32)

    def add(self, poll, cell, value):
        """ Setter method for sparse grid emissions """
        if poll not in self.pollutants:
            self.pollutants.add(poll)
            self._data[poll] = np.zeros((self.nrows, self.ncols), dtype=np.float32)

        self._data[poll][cell] += value

    def add_nocheck(self, poll, cell, value):
        """ Setter method for sparse grid emissions
            NOTE: This method is naive in that it does no checking to see if the pollutant
                  already exists or is the correct dimensions. This is a faster version of
                  the method, but more dangerous if you are not doing these checks elsewhere.
        """
        self._data[poll][cell] += value

    def add_grid(self, poll, grid):
        """ Add an entire grid of pollutant emissions to an existing pollutant.
        """
        if poll not in self.pollutants:
            self.pollutants.add(poll)
            self._data[poll] = np.zeros((self.nrows, self.ncols), dtype=np.float32)

        if grid.shape != (self.nrows, self.ncols):
            raise ValueError('Arrays has the wrong dimensions: ' + str(grid.shape))
        self._data[poll] += grid

    def add_grid_nocheck(self, poll, grid):
        """ Add an entire grid of pollutant emissions to an existing pollutant.
            NOTE: This method is naive in that it does no checking to see if the pollutant
                  already exists or is the correct dimensions. This is a faster version of
                  the method, but more dangerous if you are not doing these checks elsewhere.
        """
        self._data[poll] += grid

    def add_subgrid(self, poll, subgrid, min_row, max_row, min_col, max_col):
        """ Add a subgrid of emissions to a particular pollutant.
        """
        if poll not in self.pollutants:
            self.pollutants.add(poll)
            self._data[poll] = np.zeros((self.nrows, self.ncols), dtype=np.float32)

        self._data[poll][min_row:max_row, min_col:max_col] += subgrid

    def add_subgrid_nocheck(self, poll, subgrid, min_row, max_row, min_col, max_col):
        """ Add a subgrid of emissions to a particular pollutant.
            NOTE: This method is naive in that it does no checking to see if the pollutant
                  already exists or is the correct dimensions. This is a faster version of
                  the method, but more dangerous if you are not doing these checks elsewhere.
        """
        self._data[poll][min_row:max_row, min_col:max_col] += subgrid

    def join(self, se):
        """ add another sparse emissions object to this one """
        for poll in self.pollutants.intersection(se.pollutants):
            self._data[poll] += se._data[poll]

        for poll in se.pollutants.difference(self.pollutants):
            self.pollutants.add(poll)
            self._data[poll] = se._data[poll]

    def scale(self, factor):
        """ Scale all of the emissions in this grid by the given factor """
        for poll in self.pollutants:
            self._data[poll] *= np.float32(factor)

    def copy(self):
        """ create a deep copy of this object """
        e = SparseEmissions(self.nrows, self.ncols)
        e.pollutants = set(self.pollutants)

        for poll in self.pollutants:
            e._data[poll] = self._data[poll].copy()

        return e

    def iteritems(self):
        """ Returning the iterator object for the data, without exposing the dictionary
        """
        return self._data.iteritems()

    def __repr__(self):
        """ standard Python helper to allower for str(x) and print(x) """
        return self.__class__.__name__ + '(' + \
            str(dict((k, str(v)) for k, v in self._data.iteritems()))[1: -1] + ')'
