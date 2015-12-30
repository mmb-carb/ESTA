

class ScaledEmissions(object):
    """ This class is designed as a helper to organize the emissions by pollutant and EIC
        after they are gridded and scaled.
        This is just a multiply-embedded dictionary with keys fore:
        county, date, hr, and EIC,
        And values are just: Sparce-Grid Emissions
    """

    def __init__(self):
        self.data = {}

    def get(self, county, date, hr, eic):
        """ Getter method for the scaled emissions inventory """
        return self.data.get(county, {}).get(date, {}).get(hr, {}).get(eic, {})

    def set(self, county, date, hr, eic, grid):
        """ Setter method for the scaled emissions inventory """
        # type validation
        if type(table) != SparceEmissions:
            raise TypeError('Only sparce-grid emissions can be in the scaled emissions inventory.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if county not in self.data:
            self.data[county] = {}
        if date not in self.data[county]:
            self.data[county][date] = {}
        if hr not in self.data[county][date]:
            self.data[county][date][hr] = {}

        # add emissions
        if eic not in self.data[county][date][hr]:
            self.data[county][date][hr][eic] = grid
        else:
            self.data[county][date][hr][eic].add_grid(table)
