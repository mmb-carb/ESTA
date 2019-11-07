
from datetime import datetime as dt
import os
from os.path import basename
from netCDF4 import Dataset
import numpy as np
import time
from src.core.output_files import OutputFiles, build_arb_file_path
from src.core.output_writer import OutputWriter
from src.core.version import __version__ as version


class CmaqNetcdfWriter(OutputWriter):
    """ A class to write CMAQ-read NetCDF file.
        NOTE: This class currently only supports 2D emissions.
    """

    def __init__(self, config, position):
        super(CmaqNetcdfWriter, self).__init__(config, position)
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.version = self.config['Output'].get('inventory_version', '')
        self.spec_version = self.config['Output'].get('speciation_version', '')
        self.grid_size = int(self.config['GridInfo']['grid_size'])
        self.species = set()
        self.num_species = -1
        self.units = self.load_gspro(self.config['Output']['gspro_file'])
        self.drop_polls = ['PM10', 'PM25']

        # build some custom text to put in the NetCDF header
        file_desc = "regions: " + ' '.join([str(r) for r in self.regions]) + \
                    ", gspro: " + basename(self.config['Output']['gspro_file'])
        if self.spec_version:
            file_desc += ", speciation version: " + self.spec_version
        if self.version:
            file_desc += ", inventory version: " + self.version
        history = "gridded on-road emissions, created by the ESTA model v" + \
                  version + " on " + dt.strftime(dt.now(), '%Y-%m-%d')

        # default NetCDF header for on-road emissions on California's 4km modeling domain
        self.header = {'IOAPI_VERSION': "$Id: @(#) ioapi library version 3.1 $" + " "*43,
                       'EXEC_ID': "????????????????" + " "*64,
                       'FTYPE': 1,               # file type ID
                       'STIME': 80000,           # start time    e.g. 80000 (for GMT)
                       'TSTEP': 10000,           # time step     e.g. 10000 (1 hour)
                       'NTHIK': 1,               # Domain: perimeter thickness (boundary files only)
                       'NCOLS': self.ncols,      # Domain: number of columns in modeling domain
                       'NROWS': self.nrows,      # Domain: number of rows in modeling domain
                       'NLAYS': 1,               # Domain: number of vertical layers
                       'GDTYP': 2,               # Domain: grid type ID (lat-lon, UTM, RADM, etc...)
                       'P_ALP': 30.0,            # Projection: alpha
                       'P_BET': 60.0,            # Projection: betha
                       'P_GAM': -120.5,          # Projection: gamma
                       'XCENT': -120.5,          # Projection: x centroid longitude
                       'YCENT': 37.0,            # Projection: y centroid latitude
                       'XORIG': -684000.0,       # Domain: -684000 for CA_4k, -84000 for SC_4k
                       'YORIG': -564000.0,       # Domain: -564000 for CA_4k, -552000 for SC_4k
                       'XCELL': float(self.grid_size),  # Domain: x cell width in meters
                       'YCELL': float(self.grid_size),  # Domain: y cell width in meters
                       'VGTYP': 2,                      # Domain: grid type ID (lat-lon, UTM, RADM, etc...)
                       'VGTOP': np.float32(10000.0),         # Domain: Top Vertical layer at 10km
                       'VGLVLS': np.float32([1.0, 0.9958]),  # Domain: Vertical layer locations
                       'GDNAM': "CMAQ Emissions  ",
                       'UPNAM': "ESTA            ",
                       'FILEDESC': file_desc,
                       'HISTORY': history}
        self._config_header()

    def _config_header(self):
        ''' See if any of the above header fields are in the config object. If so, use them. '''
        for key in self.header:
            if key not in self.config['Output']:
                continue
            if type(self.header[key]) == list:
                self.header[key] = map(float, self.config['Output'][key].split())
            elif type(self.header[key]) == float:
                self.header[key] = float(self.config['Output'][key])
            elif type(self.header[key]) == int:
                self.header[key] = int(self.config['Output'][key])
            else:
                self.header[key] = self.config['Output'][key]

    def write(self, scaled_emissions):
        """ Master write method to turn the gridded emissions into NetCDF files.
        """
        # find all the input pollutants
        self.species = scaled_emissions.pollutants()
        if self.config['Output']['dpmout']:
            self.species = set([x for x in list(self.species) if x not in self.drop_polls])
        self.num_species = len(self.species)

        # find all dates with emissions data
        dates = set()
        for region_data in scaled_emissions.data.itervalues():
            for date in region_data:
                dates.add(date)
        dates = sorted(dates)

        # loop through each date
        last_date = dates[-1]
        out_paths = OutputFiles()
        for date in dates:
            out_paths[date[5:]] += self._write_netcdf(scaled_emissions, date, date == last_date)

        return out_paths

    def _write_netcdf(self, scaled_emissions, date, is_last_date):
        ''' A helper method to spread the work of creating a CMAQ-ready NetCDF file
            into more than one method. There is a lot of boilerplate to deal with.
        '''
        # re-write date in Julian date format
        d = dt.strptime(date, self.date_format)
        jdate = int(str(d.year) + dt(self.base_year, d.month, d.day).strftime('%j'))

        # final output file path
        out_path = build_arb_file_path(dt.strptime(date, self.date_format), 'ncf', self.grid_size,
                                       self.directory, self.base_year, self.start_date.year,
                                       self.version)
        print('    + writing: ' + out_path)

        # create empty netcdf file (including file path)
        rootgrp, gmt_shift = self._create_netcdf(out_path, jdate)

        # fill netcdf file with data
        self._fill_grid(scaled_emissions, date, rootgrp, gmt_shift)

        # compress output file
        if is_last_date:
            os.system('gzip -1 ' + out_path)
        else:
            os.system('gzip -1 ' + out_path + ' &')

        return [out_path + '.gz']

    def _create_netcdf(self, out_path, jdate):
        ''' Creates a blank CMAQ-ready NetCDF file, including all the important
            boilerplate and header information. But does not fill in any emissions data.
        '''
        # define some header variables
        current_date = int(time.strftime("%Y%j"))
        current_time = int(time.strftime("%H%M%S"))

        # create and outline NetCDF file
        rootgrp = Dataset(out_path, 'w', format='NETCDF3_CLASSIC')
        _ = rootgrp.createDimension('TSTEP', None)
        _ = rootgrp.createDimension('DATE-TIME', 2)
        _ = rootgrp.createDimension('LAY', 1)
        _ = rootgrp.createDimension('VAR', self.num_species)  # number of variables/species
        _ = rootgrp.createDimension('ROW', self.nrows)        # Domain: number of rows
        _ = rootgrp.createDimension('COL', self.ncols)        # Domain: number of columns

        # define TFLAG Variable
        TFLAG = rootgrp.createVariable('TFLAG', 'i4', ('TSTEP', 'VAR', 'DATE-TIME',), zlib=False)
        TFLAG.units = '<YYYYDDD,HHMMSS>'
        TFLAG.long_name = 'TFLAG'
        TFLAG.var_desc = 'Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS'

        # define variables and attribute definitions
        varl = ''
        for spec in self.species:
            units = self.units[spec]
            rootgrp.createVariable(spec, 'f4', ('TSTEP', 'LAY', 'ROW', 'COL'), zlib=False)
            rootgrp.variables[spec].long_name = spec
            rootgrp.variables[spec].units = units
            rootgrp.variables[spec].var_desc = 'emissions'
            varl += spec.ljust(16)

        # global attributes
        rootgrp.IOAPI_VERSION = self.header['IOAPI_VERSION']
        rootgrp.EXEC_ID = self.header['EXEC_ID']
        rootgrp.FTYPE = self.header['FTYPE']    # file type ID
        rootgrp.CDATE = current_date            # current date  e.g. 2013137
        rootgrp.CTIME = current_time            # current time  e.g. 50126
        rootgrp.WDATE = current_date            # current date  e.g. 2013137
        rootgrp.WTIME = current_time            # current time  e.g. 50126
        rootgrp.SDATE = jdate                   # scenario date e.g. 2010091
        rootgrp.STIME = self.header['STIME']    # start time    e.g. 80000 (for GMT)
        rootgrp.TSTEP = self.header['TSTEP']    # time step     e.g. 10000 (1 hour)
        rootgrp.NTHIK = self.header['NTHIK']    # Domain: perimeter thickness (boundary files only)
        rootgrp.NCOLS = self.header['NCOLS']    # Domain: number of columns in modeling domain
        rootgrp.NROWS = self.header['NROWS']    # Domain: number of rows in modeling domain
        rootgrp.NLAYS = self.header['NLAYS']    # Domain: number of vertical layers
        rootgrp.NVARS = self.num_species        # number of variables/species
        rootgrp.GDTYP = self.header['GDTYP']    # Domain: grid type ID (lat-lon, UTM, RADM, etc...)
        rootgrp.P_ALP = self.header['P_ALP']    # Projection: alpha
        rootgrp.P_BET = self.header['P_BET']    # Projection: betha
        rootgrp.P_GAM = self.header['P_GAM']    # Projection: gamma
        rootgrp.XCENT = self.header['XCENT']    # Projection: x centroid longitude
        rootgrp.YCENT = self.header['YCENT']    # Projection: y centroid latitude
        rootgrp.XORIG = self.header['XORIG']    # Domain: -684000 for CA_4k, -84000 for SC_4k
        rootgrp.YORIG = self.header['YORIG']    # Domain: -564000 for CA_4k, -552000 for SC_4k
        rootgrp.XCELL = self.header['XCELL']    # Domain: x cell width in meters
        rootgrp.YCELL = self.header['YCELL']    # Domain: y cell width in meters
        rootgrp.VGTYP = self.header['VGTYP']    # Domain: grid type ID (lat-lon, UTM, RADM, etc...)
        rootgrp.VGTOP = self.header['VGTOP']    # Domain: Top Vertical layer at 10km
        rootgrp.VGLVLS = self.header['VGLVLS']  # Domain: Vertical layer locations
        rootgrp.GDNAM = self.header['GDNAM']
        rootgrp.UPNAM = self.header['UPNAM']
        rootgrp.FILEDESC = self.header['FILEDESC']
        rootgrp.HISTORY = self.header['HISTORY']
        rootgrp.setncattr('VAR-LIST', varl)     # use this b/c the library does not like hyphens

        # seconds since epoch
        secs = time.mktime(time.strptime("%s 12" % jdate, "%Y%j %H"))
        gmt_shift = time.strftime("%H", time.gmtime(secs))
        secs -= (int(gmt_shift) - 8) * 3600

        # build TFLAG variable
        tflag = np.ones((25, self.num_species, 2), dtype=np.int32)
        for hr in xrange(25):
            gdh = time.strftime("%Y%j %H0000", time.gmtime(secs + hr * 3600))
            a_date, ghr = map(int, gdh.split())
            tflag[hr,:,0] = tflag[hr,:,0] * a_date
            tflag[hr,:,1] = tflag[hr,:,1] * ghr
        rootgrp.variables['TFLAG'][:] = tflag

        return rootgrp, gmt_shift

    def _fill_grid(self, scaled_emissions, date, rootgrp, gmt_shift):
        ''' Fill the entire modeling domain with a 3D grid for each pollutant.
            Fill the emissions values in each grid cell, for each polluant.
            Create a separate grid set for each date.
        '''
        # loop through the different levels of the scaled emissions dictionary
        region_data = scaled_emissions.data[-999]  # -999 is default EIC for pre-speciated emissions
        day_data = region_data.get(date, {})
        for hour, hr_data in day_data.iteritems():
            # hr should start with 0, not 1
            hr = hour - 1
            # adjust hr for DST
            if gmt_shift == '19':
                hr = (hr - 1) % 24

            sparse_emis = hr_data[-999]

            for poll in sparse_emis.pollutants:
                if poll.upper() in self.drop_polls:
                    continue
                if poll.upper() not in rootgrp.variables:
                    print('No variable for: ' + poll.upper())
                    continue

                grid = sparse_emis.get_grid(poll)
                rootgrp.variables[poll.upper()][hr,0,:,:] = grid

                if not hr:
                    rootgrp.variables[poll.upper()][24,0,:,:] = grid

        rootgrp.close()

    @staticmethod
    def load_gspro(file_path):
        ''' Grab the units for each species from the GSPRO file
            File Format:  profile, group, species, mole fraction, molecular weight=1, mass fraction
            1,TOG,CH4,3.1168E-03,1,0.0500000
            1,TOG,ALK3,9.4629E-03,1,0.5500000
            1,TOG,ETOH,5.4268E-03,1,0.2500000
        '''
        units = {}

        f = open(file_path, 'r')
        for line in f.xreadlines():
            # parse line
            ln = line.rstrip().split(',')
            group = ln[1].upper()
            species = ln[2].upper()

            if group in ['PM', 'PM10', 'PM25', 'DPM', 'DPM10', 'DPM25']:
                units[species] = 'g/s'
            else:
                units[species] = 'moles/s'

        f.close()
        return units
