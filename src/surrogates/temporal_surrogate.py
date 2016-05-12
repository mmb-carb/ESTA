
from array import array


class TemporalSurrogate(array):
    """ This is an array of 24 hourly values for one day.
        You must first fill this object with data, then use the `.surrogate()` method
        to return a new version of the object where all 24 values sum to 1.0.
    """

    def __new__(cls):
        return array.__new__(cls, 'f', [0.0]*24)

    def surrogate(self):
        """ Return a version of this object where all the values sum to 1.0. """
        t = TemporalSurrogate()

        total = sum(array.__iter__(self))
        for i in xrange(24):
            t[i] = self.__getitem__(i) / total

        return t

    def __repr__(self):
        return array.__repr__(self).replace('array', self.__class__.__name__, 1)
