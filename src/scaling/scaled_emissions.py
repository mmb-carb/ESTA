
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

        # auto-fill the multi-level dictionary format, to hide this from the user
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

    def add_subgrid(self, region, date, hr, eic, poll_grid, box):
        """ This is much like the default `set` method, except it only adds a small subgrid
            to the master grid of emissions for a particular pollutant.
        """
        min_row = box['lat'][0]
        max_row = box['lat'][1] + 1
        min_col = box['lon'][0]
        max_col = box['lon'][1] + 1

        for poll, subgrid in poll_grid.iteritems():
            self.data[region][date][hr][eic].add_subgrid(poll, subgrid, min_row, max_row, min_col, max_col)

    def add_subgrid_nocheck(self, region, date, hr, eic, poll_grid, box):
        """ This is much like the default `set` method, except it only adds a small subgrid
            to the master grid of emissions for a particular pollutant.
            NOTE: This method is designed to be fast, at the expensive of doing any error checking.
                  If the proper error/bounds checking is not done outside this method, it can fail.
        """
        min_row = box['lat'][0]
        max_row = box['lat'][1] + 1
        min_col = box['lon'][0]
        max_col = box['lon'][1] + 1

        for poll, subgrid in poll_grid.iteritems():
            self.data[region][date][hr][eic].add_subgrid_nocheck(poll, subgrid, min_row, max_row, min_col, max_col)

    def pollutants(self):
        """ return a set of all the pullants in all the Sparse-Grid Emissions object
            contained within this object
        """
        polls = set()
        for region_data in self.data.itervalues():
            for date_data in region_data.itervalues():
                for hr_data in date_data.itervalues():
                    for poll_grid in hr_data.itervalues():
                        polls.update(poll_grid.pollutants)

        return polls

    def __repr__(self):
        return self.__class__.__name__ + '(' + dict.__repr__(self.data)[1: -1] + ')'
