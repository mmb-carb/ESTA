
import numpy as np
from collections import defaultdict


class SpatialSurrogate(defaultdict):
    """ This is a sparse-matrix implementation of a spatial surrogate.
        It will work in any number of dimensions, as long as the coordinates are given as a tuple.
        You must first fill this object with data, then use the `.surrogate()` method to return a
        new version of the object where all the values sum to 1.0.
    """

    def __init__(self):
        defaultdict.__init__(self, np.float32)

    def __getitem__(self, key):
        """ Setter method for spatial surrogate dictionary """
        val = defaultdict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """ Getter method for spatial surrogate dictionary """
        if type(key) != tuple:
            raise TypeError('The coordinate was not a tuple: ' + str(key))
        defaultdict.__setitem__(self, key, val)

    def surrogate(self):
        """ A simple helper method to return a version of this object
            where all the values sum to 1.0.
        """
        total = np.sum(defaultdict.values(self))

        if total == 1.0:
            return self
        elif total:
            # The easy situation: just normalize all the values so they sum to 1.0
            for key, value in self.iteritems():
                self.__setitem__(key, value / total)
        else:
            # What if the total is zero?
            number_keys = defaultdict.__len__(self)
            if number_keys:
                return defaultdict(lambda: np.float32(1.0 / number_keys))

        return self

    def __repr__(self):
        return self.__class__.__name__ + '(' + str(dict(self))[1: -1] + ')'

