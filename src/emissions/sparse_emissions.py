
import numpy as np


class SparseEmissions(object):
    """ This is a sparce-grid representation of emissions on a grid.
        For every pollutant there is a NumPy array representing the
        emissions in each cell of the grid.
        This grid represents all the emissions for a single EIC during a single hour.
    """

    def __init__(self, nrows, ncols):
        self._data = {}
        # TODO: This stupid mask is only for Pmeds1Writer?  Then I think we should ditch it. 
        # TODO: Or do we use "join" below a lot for the NetCDF?
        self.mask = set()
        self.pollutants = set()
        self.nrows = nrows
        self.ncols = ncols

    def get(self, poll, cell):
        """ Getter method for sparse grid emissions """
        return self._data[poll][cell]

    def get_grid(self, poll):
        """ Get a copy of an entire pollutant grid """
        return self._data[poll].copy()

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
        self.mask.add(cell)

    def add_naive(self, poll, cell, value):
        """ Setter method for sparse grid emissions
            This makes the naive assumption that the pollutant is already part of this object.
            This method can fail hard, and is meant to be used in conjunction with pre-processing
            to aid in performance.
        """
        self._data[poll][cell] += value
        self.mask.add(cell)

    def join(self, se):
        """ add another sparse emissions object to this one """
        self.mask = self.mask.union(se.mask)

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

    def __repr__(self):
        """ standard Python helper to allower for str(x) and print(x) """
        return self.__class__.__name__ + '(' + \
            str(dict((k, str(v)) for k, v in self._data.iteritems()))[1: -1] + ')'
