
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
        total = sum(defaultdict.values(self))
        if total == 1.0:
            # already normalized
            return self

        s = SpatialSurrogate()
        if total:
            # The easy situation, just normalize all the values so they sum to 1.0.
            for key in defaultdict.__iter__(self):
                s[key] = self.__getitem__(key) / total
        else:
            # What if the total is zero?
            number_keys = len(list(defaultdict.values(self)))
            if number_keys:
                # This only works for non-zero number of keys.
                s = dict(zip(defaultdict.__iter__(self), [1.0 / number_keys]*number_keys))

        return s

    def __repr__(self):
        return defaultdict.__repr__(self).replace('defaultdict', self.__class__.__name__, 1)

