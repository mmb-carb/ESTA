
from collections import defaultdict


class OutputFiles(defaultdict):
    """ A simple collection of output files, created by ESTA, organized by date. """

    def __init__(self):
        defaultdict.__init__(self, list)

    def __getitem__(self, key):
        """ Getter method """
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        """ Setter method """
        if type(key) != str or type(val) != list:
            raise TypeError('The key of the OutputFiles object must be a date string ' +
                            'and value must be a file path.')
        defaultdict.__setitem__(self, key, val)

    def union(self, new_files):
        """ Combine this object with another of the same type """
        if type(new_files) != self.__class__:
            raise TypeError('Only ' + self.__class__.__name__ + ' objects can be unioned together.')

        for date, file_paths in new_files.iteritems():
            for file_path in file_paths:
                defaultdict.__setitem__(self, date, defaultdict.__getitem__(self, date) + [file_path])
