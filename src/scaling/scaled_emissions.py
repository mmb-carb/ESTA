
from src.emissions.sparse_emissions import SparseEmissions


class ScaledEmissions(object):
    """ This class is designed as a helper to organize the emissions by pollutant and EIC
        after they are gridded and scaled.
        This is just a multiply-embedded dictionary with keys fore:
        region, date, hr, and EIC,
        And values are just: Sparse-Grid Emissions
    """

    def __init__(self):
        self.data = {}

    def get(self, region, date, hr, eic):
        """ Getter method for the scaled emissions inventory """
        return self.data.get(region, {}).get(date, {}).get(hr, {}).get(eic, {})

    def set(self, region, date, hr, eic, poll_grid):
        """ Setter method for the scaled emissions inventory """
        # type validation
        if type(poll_grid) != SparseEmissions:
            raise TypeError('Only sparse-grid emissions can be in the scaled emissions inventory.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if region not in self.data:
            self.data[region] = {}
        if date not in self.data[region]:
            self.data[region][date] = {}
        if hr not in self.data[region][date]:
            self.data[region][date][hr] = {}

        # add emissions
        if eic not in self.data[region][date][hr]:
            self.data[region][date][hr][eic] = poll_grid
        else:
            self.data[region][date][hr][eic].join(poll_grid)

    def __repr__(self):
        return self.__class__.__name__ + '(' + dict.__repr__(self.data)[1: -1] + ')'
