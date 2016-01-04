
from datetime import datetime as dt
from output_writer import OutputWriter


class Pmeds1Writer(OutputWriter):
    """
    """

    def __init__(self, config, directory, time_units):
        super(Pmeds1Writer, self).__init__(config, directory, time_units)
        self.date_format = self.config['Dates']['format']
        self.start_date = dt.strptime(self.config['Dates']['start'], self.date_format)
        self.end_date = dt.strptime(self.config['Dates']['end'], self.date_format)
        self.base_year = int(self.config['Dates']['base_year'])
        self.counties = Pmeds1Writer.parse_counties(self.config['Subareas']['subareas'])

    def write(self, scaled_emissions):
        """ The master method to write output files.
            In this case, we are writing one file per county.
        """
        for county in self.counties:
            self._write_county_pmeds1(county, scaled_emissions)

    def _write_county_pmeds1(self, county, scaled_emissions):
        """
        """
        pass

    @staticmethod
    def parse_counties(counties_str):
        """ Parse the string we get back from the subareas field """
        if '..' in counties_str:
            counties = counties_str.split('..')
            counties = range(int(counties[0]), int(counties[1]))
        else:
            counties = [int(c) for c in counties_str.split()]

        return counties
