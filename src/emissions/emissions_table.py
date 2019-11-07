
from collections import defaultdict
import numpy as np


class EmissionsTable(defaultdict):
    """ An emissions table object stores emissions values (unitless floats)
        by two indicies: EIC and then pollutant.
        To support different models, there is no restriction on the type
        used to define EICs or pollutants.
    """

    def __init__(self):
        defaultdict.__init__(self, lambda: defaultdict(np.float32))

    def __getitem__(self, key):
        """ Getter method for emissions table """
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        """ Setter method for emissions table """
        if type(val) != defaultdict:
            raise TypeError('The emissions table must be two levels deep: EIC and pollutant.')
        for value in val.values():
            if type(value) != np.float32:
                raise TypeError('Emissions values must be of type np.float32.')
        defaultdict.__setitem__(self, key, val)

    def add_table(self, table):
        """ Combine this EmissionsTable object with another """
        for eic, eic_data in table.iteritems():
            if not defaultdict.__contains__(self, eic):
                defaultdict.__setitem__(self, eic, eic_data)
            else:
                for poll, value in eic_data.iteritems():
                    eic_dict = defaultdict.__getitem__(self, eic)
                    eic_dict[poll] += value

    def __deepcopy__(self, table):
        e = EmissionsTable()
        for eic, eic_data in self.iteritems():
            for poll, value in eic_data.iteritems():
                #print poll, value  #MMD
                e[eic][poll] = value

        return e

    def __repr__(self):
        return self.__class__.__name__ + '(' + \
            str(dict((k, dict(v)) for k,v in self.iteritems()))[1: -1] + ')'
