
from src.emissions.sparce_emissions import SparceEmissions


class ScaledEmissions(object):
    """ This class is designed as a helper to organize the emissions by pollutant and EIC
        after they are gridded and scaled.
        This is just a multiply-embedded dictionary with keys fore:
        subarea, date, hr, and EIC,
        And values are just: Sparce-Grid Emissions
    """

    def __init__(self):
        self.data = {}

    def get(self, subarea, date, hr, eic):
        """ Getter method for the scaled emissions inventory """
        return self.data.get(subarea, {}).get(date, {}).get(hr, {}).get(eic, {})

    def set(self, subarea, date, hr, eic, grid):
        """ Setter method for the scaled emissions inventory """
        # type validation
        if type(grid) != SparceEmissions:
            raise TypeError('Only sparce-grid emissions can be in the scaled emissions inventory.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if subarea not in self.data:
            self.data[subarea] = {}
        if date not in self.data[subarea]:
            self.data[subarea][date] = {}
        if hr not in self.data[subarea][date]:
            self.data[subarea][date][hr] = {}

        # add emissions
        if eic not in self.data[subarea][date][hr]:
            self.data[subarea][date][hr][eic] = grid
        else:
            self.data[subarea][date][hr][eic].add_grid(grid)
