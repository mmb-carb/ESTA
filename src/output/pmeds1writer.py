
from datetime import datetime as dt
from glob import glob
import gzip
import os
from src.core.output_writer import OutputWriter


class Pmeds1Writer(OutputWriter):
    """ A class to write PMEDS v1 output files.
        One for each region/date combination.
    """

    COLUMNS = {'co': 0, 'nox': 1, 'sox': 2, 'tog': 3, 'pm': 4, 'nh3': 5}
    STONS_2_KG = 907.185

    def __init__(self, config, directory, time_units):
        super(Pmeds1Writer, self).__init__(config, directory, time_units)
        self.by_region = self.config.getboolean('Output', 'by_region')
        self.combine = self.config.getboolean('Output', 'combine_regions')
        self.version = self.config['Output']['inventory_version']
        self.grid_file = self.config['GridInfo']['grid_cross_file']
        self.region_names = self.config.eval_file('Misc', 'region_names')
        self.county_to_gai = self.config.eval_file('Output', 'county_to_gai')
        self.gai_to_county = self.config.eval_file('Output', 'gai_to_county')
        self.gai_basins = self.config.eval_file('Output', 'gai_basins')
        self.multi_gai_coords = self.config.eval_file('Output', 'multi_gai_coords')
        self.has_subregions = self.config.getboolean('Regions', 'has_subregions')

    def write(self, scaled_emissions):
        """ The master method to write output files.
            This can write output files by region, or for the entire day.
        """
        if self.by_region:
            self.write_by_region(scaled_emissions)
        else:
            self.write_by_state(scaled_emissions)

    def write_by_region(self, scaled_emissions):
        """ Write a single file for each region/date combo
        """
        for region, region_data in scaled_emissions.data.iteritems():
            for date, date_date in region_data.iteritems():
                self._write_pmeds1_by_region(scaled_emissions, region, date)

    def write_by_state(self, scaled_emissions):
        """ Write a single output file per day
        """
        # find all dates
        dates = set()
        for region, region_data in scaled_emissions.data.iteritems():
            for date in region_data:
                dates.add(date)

        # write a file for each date
        dates = sorted(dates)
        for date in dates:
            self._write_pmeds1_by_state(scaled_emissions, date)

    def _write_pmeds1_by_state(self, scaled_emissions, date):
        """ Write a single 24-hour PMEDS file for a given date, for the entire state.
            Each region might have multiple subregion, so that has to be worked out.
        """
        out_path = self._build_state_file_path(date)
        jul_day = dt.strptime(str(self.base_year) + date[4:], self.date_format).timetuple().tm_yday
        lines = []

        # loop through the different levels of the scaled emissions dictionary
        for region, region_data in scaled_emissions.data.iteritems():
            day_data = region_data.get(date, {})
            for hr, hr_data in day_data.iteritems():
                for eic, sparce_emis in hr_data.iteritems():
                    for cell, grid_data in sparce_emis.iteritems():
                        # calculate sub-regions from region and cell
                        subregions = self._find_subregion(region, cell)
                        # loop over subregions
                        for subregion, frac in subregions:
                            # build list of six pollutants
                            emis = ['', '', '', '', '', '']
                            no_emissions = True
                            for poll, value in grid_data.iteritems():
                                try:
                                    col = Pmeds1Writer.COLUMNS[poll.lower()]
                                except:
                                    # irrelevant pollutant
                                    continue
                                val = '{0:.5f}'.format(value * frac * self.STONS_2_KG).rstrip('0')
                                if val != '0.':
                                    emis[col] = val
                                    no_emissions = False

                            # if there are emissions, build PMEDS line
                            if no_emissions:
                                continue
                            lines.append(self._build_pmeds1_line(region, subregion, date, jul_day,
                                                                 hr, eic, cell, emis))

        if lines:
            self._write_zipped_file(out_path, lines)

    def _write_pmeds1_by_region(self, scaled_emissions, region, date):
        """ Write a single 24-hour PMEDS file for a given region/date combination.
            Each region might have multiple COABDIS, so that has to be worked out.
        """
        out_path = self._build_regional_file_path(region, date)
        jul_day = dt.strptime(str(self.base_year) + date[4:], self.date_format).timetuple().tm_yday
        lines = []

        for hr, hr_data in scaled_emissions.data[region][date].iteritems():
            for eic, sparce_emis in hr_data.iteritems():
                for cell, grid_data in sparce_emis.iteritems():
                    # calculate subregion from region and cell
                    subregions = self._find_subregion(region, cell)
                    # loop over subregions
                    for subregion, frac in subregions:
                        # build list of six pollutants
                        emis = ['', '', '', '', '', '']
                        no_emissions = True
                        for poll, value in grid_data.iteritems():
                            try:
                                col = Pmeds1Writer.COLUMNS[poll.lower()]
                            except:
                                # irrelevant pollutant
                                continue
                            val = '{0:.5f}'.format(value * frac * self.STONS_2_KG).rstrip('0')
                            if val != '0.':
                                emis[col] = val
                                no_emissions = False

                        # if there are emissions, build PMEDS line
                        if no_emissions:
                            continue
                        lines.append(self._build_pmeds1_line(region, subregion, date, jul_day, hr,
                                                             eic, cell, emis))

        self._write_file(out_path, lines)
        self._combine_regions(date)

    def _combine_regions(self, date):
        ''' If all the region files have been written, this will cat them all
            together into one big file.
        '''
        if not self.combine:
            return

        # new output file path
        out_file = self._build_state_file_path(date) + '.gz'

        # use glob to count files in the output folder
        yr, month, day = date.split('-')
        region_paths = os.path.join(self.directory, month, day, '*.pmeds')
        region_files = glob(region_paths)

        # if all regions are finished, zcat results together
        if len(region_files) != len(self.regions):
            return
        print('    + writing: ' + out_file)
        os.system('cat ' + ' '.join(region_files) + ' | gzip -9c > ' + out_file)

        # remove old region files
        os.system('rm ' + ' '.join(region_files) + ' &')

    def _build_pmeds1_line(self, region, gai, date, jul_day, hr, eic, grid_cell, emis):
        """ Build the complicated PMEDS v1 line from available data
            Line Format:
            Amador                71074211000000162179               3122001313 MC  7     ,,,,0.024,
            Los Ange              71074211000000165180               3122000707 MC  7     ,,,0.008,,
            Alpine                71074211000000183190               2122001414GBV  1     0.015,,,,,
        """
        # define parameters
        yr = date[2:4]
        if self.has_subregions:
            county_name = self.region_names[region][:8].ljust(8)
        else:
            county_name = self.region_names[region][:8].ljust(8)
        y, x = grid_cell
        hour = '%02d%02d' % (hr - 1, hr - 1)
        basin = self.gai_basins[gai].rjust(3)
        emissions = ','.join(emis)
        county = self.gai_to_county[gai]

        return ''.join([county_name, str(eic).rjust(28), str(x).rjust(3), str(y).rjust(3),
                        '              ', str(county).rjust(2), yr, str(jul_day).rjust(3), hour,
                        basin, str(gai).rjust(3), '     ', emissions, '\n'])

    def _write_zipped_file(self, out_path, lines):
        """ simple helper method to write a list of strings to a gzipped file """
        if not self.combine:
            print('    + writing: ' + out_path + '.gz')

        f = gzip.open(out_path + '.gz', 'wb')
        try:
            f.writelines(lines)
        finally:
            f.close()

    def _write_file(self, out_path, lines):
        """ simple helper method to write a list of strings to a file """
        if not self.combine:
            print('    + writing: ' + out_path)

        f = open(out_path, 'w')
        try:
            f.writelines(lines)
        finally:
            f.close()

    def _find_subregion(self, region, grid_cell):
        """ Find the sub-regions related to the given grid cell.
            Since we know the region, this is very easy for the regions that match 1-to-1 with
            a sub-region. Otherwise, we have to use a look-up table, by grid cell.
        """
        # emissions area already by GAI, not county
        if not self.has_subregions:
            return [[region, 1.0]]

        subregion_list = self.county_to_gai[region]

        if len(subregion_list) == 1:
            # the easy regions
            return [[subregion_list[0], 1.0]]
        elif grid_cell in self.multi_gai_coords[region]:
            # the multi-sub-region regions
            return self.multi_gai_coords[region][grid_cell]
        else:
            # multi-subregion grid cell not found, use default sub-region in region
            return [[subregion_list[0], 1.0]]

    def _build_regional_file_path(self, region, date):
        """ build output file directory and path for PMEDS file """
        yr, month, day = date.split('-')

        out_dir = os.path.join(self.directory, month, day)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        nomen = self.region_names[region].replace(')', '').replace('(', '').replace(' ', '_')
        return os.path.join(out_dir, nomen + '.pmeds')

    def _build_state_file_path(self, date):
        """ Build output file directory and path for a daily, multi-region PMEDS file.
            NOTE: This method uses an extremely detailed file naming convention.
                  For example:
            st_4k.mv.v0938..2012.203107d18..e14..pmeds
            [statewide]_[4km grid].[mobile source].[version 938]..[base year 2012].
            [model year 2031][month 7]d[day 18]..[EIC 14 categories]..[PMEDS format]
        """
        yr, month, day = date.split('-')

        out_dir = os.path.join(self.directory, 'pmeds')
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # define the grid size string
        grid_size = '4k'
        grid_name = os.path.basename(self.grid_file)
        if '12km' in grid_name:
            grid_size = '12k'
        elif '36km' in grid_name:
            grid_size = '36k'
        elif '1km' in grid_name:
            grid_size = '1k'
        elif '250m' in grid_name:
            grid_size = '250m'

        # TODO: "st" = state, "mv" = mobile, and "e14" = EIC-14 All can change
        file_name = 'st_' + grid_size + '.mv.' + self.version + '..' + str(self.base_year) + '.' + \
                    yr + month + 'd' + day + '..e14..pmeds'

        return os.path.join(out_dir, file_name)
