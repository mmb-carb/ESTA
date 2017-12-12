
from datetime import datetime as dt
from glob import glob
import gzip
import numpy as np
import os
from src.core.output_files import OutputFiles, build_arb_file_path
from src.core.output_writer import OutputWriter


class CseWriter(OutputWriter):
    """ A class to write CSE output files.
        One for each region/date combination.
    """

    COLUMNS = {'CO': 0, 'NOX': 1, 'SOX': 2, 'TOG': 3, 'PM': 4, 'NH3': 5}
    STONS_2_KG = np.float32(907.185)
    MIN_EMIS = np.float32(5e-6) / STONS_2_KG

    def __init__(self, config, position):
        super(CseWriter, self).__init__(config, position)
        self.version = self.config['Output'].get('inventory_version', '')
        self.grid_size = int(self.config['GridInfo']['grid_size'])
        self.region_boxes = self.config.eval_file('Surrogates', 'region_boxes')  # bounds are inclusive
        # parse and format specialized region info for CSE files
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
        out_paths = OutputFiles()
        for region, region_data in scaled_emissions.data.iteritems():
            for date, hourly_emis in region_data.iteritems():
                new_files = self._write_cse_by_region(hourly_emis, region, date)
                if new_files:
                    out_paths[date[5:]] += new_files

        return out_paths

    def _write_cse_by_region(self, hourly_emis, region, date):
        """ Write a single 24-hour CSE file for a given region/date combination.
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

                        # build CSE line
                        if emis_found:
                            f.write(self._build_cse_line(region, date, jul_day, hr, eic, (i, j), emis))

        f.close()
        return self._combine_regions(date, out_path)

    def _combine_regions(self, date, out_path):
        ''' If all the region files have been written, this will cat them all
            together into one big file.
        '''
        # new output file path
        out_file = build_arb_file_path(dt.strptime(date, self.date_format), 'cse', self.grid_size,
                                       self.directory, self.base_year, self.start_date.year,
                                       self.version)

        # use glob to count files in the output folder
        yr, month, day = date.split('-')
        region_paths = os.path.join(self.directory, month, day, '*.cse')
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

    def _build_cse_line(self, region, date, jul_day, hr, eic, grid_cell, emis):
        """ Build the complicated CSE line from available data
            Line Format: SIC,EIC/SCC,I,J,REGION,YEAR,JUL_DAY,START_HR,END_HR,CO,NOX,SOX,TOG,PM,NH3
            ,71074211000000,62,79,3,12,200,13,13,,,,,0.024,
            ,71074211000000,165,180,3,12,200,07,07,,,,0.008,,
            ,71074211000000,183,190,2,12,200,14,14,0.000000005,,,,,
        """
        y, x = grid_cell
        hour = str(hr - 1)
        emissions = ','.join(emis)
        yr = str(self.start_date.year)[2:4]

        return ','.join(['', str(eic), str(x + 1), str(y + 1), str(region), yr, jul_day, hour, hour, emissions]) + '\n'

    def _build_regional_file_path(self, region, date):
        """ build output file directory and path for CSE file """
        yr, month, day = date.split('-')

        out_dir = os.path.join(self.directory, month, day)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        nomen = self.region_names[region].replace(')', '').replace('(', '').replace(' ', '_')
        return os.path.join(out_dir, nomen + '.cse')
