
from collections import defaultdict


class SpatialSurrogate(defaultdict):
    """ This is a sparse-matrix implementation of a spatial surrogate.
        It will work in any number of dimensions, as long as the coordinates are given as a tuple.
        You must first fill this object with data, then use the `.surrogate()` method to return a
        new version of the object where all the values sum to 1.0.
    """
    def __init__(self):
        defaultdict.__init__(self, float)

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
        s = SpatialSurrogate()

        total = sum(defaultdict.values(self))
        for key in defaultdict.__iter__(self):
            s[key] = self.__getitem__(key) / total

        return s

    # TODO: Override 'type', 'str', and 'repr' methods.
