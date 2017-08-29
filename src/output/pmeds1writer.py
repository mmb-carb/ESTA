
from datetime import datetime as dt
from glob import glob
import gzip
import numpy as np
import os
from src.core.output_files import OutputFiles, build_arb_file_path
from src.core.output_writer import OutputWriter


class Pmeds1Writer(OutputWriter):
    """ A class to write PMEDS v1 output files.
        One for each region/date combination.
    """

    COLUMNS = {'co': 0, 'nox': 1, 'sox': 2, 'tog': 3, 'pm': 4, 'nh3': 5}
    STONS_2_KG = np.float32(907.185)
    MIN_EMIS = np.float32(5e-6) / STONS_2_KG

    def __init__(self, config, position):
        super(Pmeds1Writer, self).__init__(config, position)
        self.version = self.config['Output']['inventory_version']
        self.grid_file = self.config['GridInfo']['grid_cross_file']
        self.region_boxes = self.config.eval_file('Surrogates', 'region_boxes')  # bounds are inclusive
        self.by_region = self.config.getboolean('Output', 'by_region')
        self.combine = self.config.getboolean('Output', 'combine_regions') if self.by_region else False
        # parse and format specialized region info for PMEDS files
        self.region_info = self.config.eval_file('Regions', 'region_info')
        self.gai_to_county = dict((g, str(d['county']).rjust(2)) for g,d in self.region_info.iteritems())
        self.gai_basins = dict((g, d['air_basin'].rjust(3)) for g,d in self.region_info.iteritems())
        self.region_names = dict((g, d['name']) for g,d in self.region_info.iteritems())
        self.short_region_names = dict((g, d['name'][:8].ljust(8)) for g,d in self.region_info.iteritems())
        self.short_regions = dict((g, str(g).rjust(3)) for g in self.region_info)

    def write(self, scaled_emissions):
        """ The master method to write output files.
            This can write output files by region, or for the entire day.
        """
        if self.by_region:
            return self.write_by_region(scaled_emissions)
        else:
            return self.write_by_state(scaled_emissions)

    def write_by_region(self, scaled_emissions):
        """ Write a single file for each region/date combo
        """
        out_paths = OutputFiles()
        for region, region_data in scaled_emissions.data.iteritems():
            for date, hourly_emis in region_data.iteritems():
                new_files = self._write_pmeds1_by_region(hourly_emis, region, date)
                if new_files:
                    out_paths[date[5:]] += new_files

        return out_paths

    def write_by_state(self, scaled_emissions):
        """ Write a single output file per day
        """
        # find all dates
        dates = set()
        for region_data in scaled_emissions.data.itervalues():
            for date in region_data:
                dates.add(date)

        # write a file for each date
        dates = sorted(dates)
        out_paths = OutputFiles()
        for date in dates:
            out_paths[date[5:]] += self._write_pmeds1_by_state(scaled_emissions, date)

        return out_paths

    def _write_pmeds1_by_state(self, scaled_emissions, date):
        """ Write a single 24-hour PMEDS file for a given date, for the entire state.
        """
        out_path = build_arb_file_path(dt.strptime(date, self.date_format), self.grid_file, 'pmeds',
                                       self.directory, self.base_year, self.start_date.year,
                                       self.version)
        jul_day = str(dt.strptime(str(self.base_year) + date[4:], self.date_format).timetuple().tm_yday).rjust(3)

        f = gzip.open(out_path, 'wb')

        # loop through the different levels of the scaled emissions dictionary
        for region, region_data in scaled_emissions.data.iteritems():
            # pull bounding box for region
            box = self.region_boxes[region]  # {'lat': (51, 92), 'lon': (156, 207)}
            x_min, x_max = box['lon']
            y_min, y_max = box['lat']
            x_max += 1
            y_max += 1
            day_data = region_data.get(date, {})
            for hr, hr_data in day_data.iteritems():
                for eic, sparse_emis in hr_data.iteritems():
                    polls = [(p, self.COLUMNS[p]) for p in sparse_emis.pollutants if p in self.COLUMNS]
                    for i in xrange(y_min, y_max):
                        for j in xrange(x_min, x_max):
                            emis_found = False
                            emis = ['', '', '', '', '', '']
                            for poll, col in polls:
                                try:
                                    value = sparse_emis.get(poll, (i, j))
                                    if value > self.MIN_EMIS:
                                        emis[col] = '%.5f' % (value * self.STONS_2_KG)
                                        emis_found = True
                                except KeyError:
                                    # pollutant not in this grid cell
                                    pass

                            # build PMEDS line
                            if emis_found:
                                f.write(self._build_pmeds1_line(region, date, jul_day, hr, eic,
                                                                (i, j), emis))

        f.close()
        return [out_path]

    def _write_pmeds1_by_region(self, hourly_emis, region, date):
        """ Write a single 24-hour PMEDS file for a given region/date combination.
            Each region might have multiple COABDIS, so that has to be worked out.
        """
        # pull bounding box for region
        box = self.region_boxes[region]  # {'lat': (51, 92), 'lon': (156, 207)}
        x_min, x_max = box['lon']
        y_min, y_max = box['lat']
        x_max += 1
        y_max += 1

        # build date strings
        out_path = self._build_regional_file_path(region, date)
        jul_day = str(dt.strptime(str(self.base_year) + date[4:], self.date_format).timetuple().tm_yday).rjust(3)

        f = open(out_path, 'w')

        for hr, hr_data in hourly_emis.iteritems():
            for eic, sparse_emis in hr_data.iteritems():
                polls = [(p, self.COLUMNS[p]) for p in sparse_emis.pollutants if p in self.COLUMNS]
                for i in xrange(y_min, y_max):
                    for j in xrange(x_min, x_max):
                        emis_found = False
                        emis = ['', '', '', '', '', '']
                        for poll, col in polls:
                            value = sparse_emis.get(poll, (i, j))
                            if value > self.MIN_EMIS:
                                emis[col] = '%.5f' % (value * self.STONS_2_KG)
                                emis_found = True

                        # build PMEDS line
                        if emis_found:
                            f.write(self._build_pmeds1_line(region, date, jul_day, hr, eic,
                                                            (i, j), emis))

        f.close()
        return self._combine_regions(date, out_path)

    def _combine_regions(self, date, out_path):
        ''' If all the region files have been written, this will cat them all
            together into one big file.
        '''
        if not self.combine:
            print('    + writing: ' + out_path)
            return [out_path]

        # new output file path
        out_file = build_arb_file_path(dt.strptime(date, self.date_format), self.grid_file,
                                       'pmeds', self.directory, self.base_year,
                                       self.start_date.year, self.version)

        # use glob to count files in the output folder
        yr, month, day = date.split('-')
        region_paths = os.path.join(self.directory, month, day, '*.pmeds')
        region_files = glob(region_paths)

        # if all regions are finished, zcat results together
        if len(region_files) != len(self.regions):
            return []
        print('    + writing: ' + out_file)
        out_file += '.gz'
        os.system('cat ' + ' '.join(region_files) + ' | gzip -9c > ' + out_file)

        # remove old region files
        os.system('rm ' + ' '.join(region_files))

        # if the directory is empty, feel free to delete it
        day_dir = os.path.dirname(region_files[0])
        if not os.listdir(day_dir):
            os.system('rm -rf ' + day_dir)

            # if the directory above THAT is empty, try deleting it
            month_dir = os.path.dirname(day_dir)
            if not os.listdir(month_dir):
                os.system('rm -rf ' + month_dir)

        return [out_file]

    def _build_pmeds1_line(self, region, date, jul_day, hr, eic, grid_cell, emis):
        """ Build the complicated PMEDS v1 line from available data
            Line Format:
            Amador                71074211000000162179               3122001313 MC  7     ,,,,0.024,
            Los Ange              71074211000000165180               3122000707 MC  7     ,,,0.008,,
            Alpine                71074211000000183190               2122001414GBV  1     0.015,,,,,
        """
        # define parameters
        y, x = grid_cell
        hour = '%02d' % (hr - 1)
        emissions = ','.join(emis)
        yr = str(self.start_date.year)[2:4]

        return ''.join([self.short_region_names[region], str(eic).rjust(28), str(x + 1).rjust(3),
                        str(y + 1).rjust(3), '              ', self.gai_to_county[region], yr,
                        jul_day, hour, hour, self.gai_basins[region], self.short_regions[region],
                        '     ', emissions, '\n'])

    def _build_regional_file_path(self, region, date):
        """ build output file directory and path for PMEDS file """
        yr, month, day = date.split('-')

        out_dir = os.path.join(self.directory, month, day)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        nomen = self.region_names[region].replace(')', '').replace('(', '').replace(' ', '_')
        return os.path.join(out_dir, nomen + '.pmeds')
