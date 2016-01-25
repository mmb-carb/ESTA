
from collections import defaultdict


class EmissionsTable(defaultdict):
    """ An emissions table object stores emissions values (unitless floats)
        by two indicies: EIC and then pollutant.
        To support different models, there is no restriction on the type
        used to define EICs or pollutants.
    """

    def __init__(self):
        defaultdict.__init__(self, lambda: defaultdict(float))

    def __getitem__(self, key):
        """ Setter method for emissions table """
        val = defaultdict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """ Getter method for emissions table """
        if type(val) != defaultdict:
            raise TypeError('The emissions table must be two levels deep: EIC and pollutant.')
        for value in val.values():
            if type(value) != float:
                raise TypeError('Emissions values must be of type float.')
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
                e[eic][poll] = value

        return e
    
    def __repr__(self):
        return defaultdict.__repr__(self).replace('defaultdict', self.__class__.__name__, 1)

