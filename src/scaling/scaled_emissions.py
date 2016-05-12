
from src.emissions.sparce_emissions import SparceEmissions


class ScaledEmissions(object):
    """ This class is designed as a helper to organize the emissions by pollutant and EIC
        after they are gridded and scaled.
        This is just a multiply-embedded dictionary with keys fore:
        region, date, hr, and EIC,
        And values are just: Sparce-Grid Emissions
    """

    def __init__(self):
        self.data = {}

    def get(self, region, date, hr, eic):
        """ Getter method for the scaled emissions inventory """
        return self.data.get(region, {}).get(date, {}).get(hr, {}).get(eic, {})

    def set(self, region, date, hr, eic, grid):
        """ Setter method for the scaled emissions inventory """
        # type validation
        if type(grid) != SparceEmissions:
            raise TypeError('Only sparce-grid emissions can be in the scaled emissions inventory.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if region not in self.data:
            self.data[region] = {}
        if date not in self.data[region]:
            self.data[region][date] = {}
        if hr not in self.data[region][date]:
            self.data[region][date][hr] = {}

        # add emissions
        if eic not in self.data[region][date][hr]:
            self.data[region][date][hr][eic] = grid
        else:
            self.data[region][date][hr][eic].add_grid(grid)

    def __repr__(self):
        return self.__class__.__name__ + '(' + dict.__repr__(self.data)[1: -1] + ')'
