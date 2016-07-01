
from datetime import datetime as dt
import gc
import os
from netCDF4 import Dataset
import numpy as np
import sys
import time
from src.core.output_writer import OutputWriter


class CmaqNetcdfWriter(OutputWriter):
    """ A class to write CMAQ-read NetCDF file.
        NOTE: This class currently only supports 2D emissions.
    """

    STONS_HR_2_G_SEC = 251.99583333333334

    def __init__(self, config, position):
        super(CmaqNetcdfWriter, self).__init__(config, position)
        self.nrows = int(self.config['GridInfo']['rows'])
        self.ncols = int(self.config['GridInfo']['columns'])
        self.version = self.config['Output']['inventory_version']
        self.grid_file = self.config['GridInfo']['grid_cross_file']
        self.gspro_file = self.config['Output']['gspro_file']
        self.gsref_file = self.config['Output']['gsref_file']
        self.weight_file = self.config['Output']['weight_file']
        self.gspro = {}
        self.gsref = {}
        self.groups = {}
        self.num_species = 0
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
                       'XCELL': 4000.0,          # Domain: x cell width in meters
                       'YCELL': 4000.0,          # Domain: y cell width in meters
                       'VGTYP': 2,               # Domain: grid type ID (lat-lon, UTM, RADM, etc...)
                       'VGTOP': 10000,           # Domain: Top Vertical layer at 10km
                       'VGLVLS': [1.0, 0.9958],  # Domain: Vertical layer locations
                       'GDNAM': "CMAQ Emissions  ",
                       'UPNAM': "combineEmis_wdwe",
                       'FILEDESC': "",
                       'HISTORY': ""}
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
        # Read speciation profiles & molecular weight files
        self._load_weight_file()
        self._load_gsref()
        self._load_gspro()

        # find all dates with emissions data
        dates = set()
        for region_data in scaled_emissions.data.itervalues():
            for date in region_data:
                dates.add(date)
        dates = sorted(dates)

        # loop through each date
        last_date = dates[-1]
        for date in dates:
            # Convert scaled_emissions dict to NetCDF-ready 2D numpy.arrays
            grid = self._fill_grid(scaled_emissions, date)

            # write NetCDF
            self._write_netcdf(grid, date, date == last_date)

    def _write_netcdf(self, grid, date, is_last_date):
        ''' A helper method to spread the work of creating a CMAQ-ready NetCDF file
            into more than one method. There is a lot of boilerplate to deal with.
        '''
        # re-write date in Julian date format
        d = dt.strptime(date, self.date_format)
        jdate = int(str(d.year) + dt(self.base_year, d.month, d.day).strftime('%j'))

        # final output file path
        out_path = self._build_state_file_path(date)
        print('    + writing: ' + out_path)

        # create empty netcdf file (including file path)
        rootgrp = self._create_netcdf(out_path, date, jdate)

        # fill netcdf file with data
        self._write_to_netcdf(rootgrp, grid, jdate)

        # compress output file
        if is_last_date:
            os.system('gzip -1 ' + out_path)
        else:
            os.system('gzip -1 ' + out_path + ' &')

    def _write_to_netcdf(self, rootgrp, grid, jdate):
        ''' Take the object representing our CMAQ-NetCDF file and fill
            in all of the emissions values.
            When finished, zip the file.
        '''
        # seconds since epoch
        secs = time.mktime(time.strptime("%s 12" % jdate, "%Y%j %H"))
        gmt_shift = time.strftime("%H", time.gmtime(secs))
        secs -= (int(gmt_shift) - 8) * 60 * 60

        # build TFLAG variable
        tflag = np.ones((25, self.num_species, 2), dtype=np.int32)
        for hr in xrange(25):
            gdh = time.strftime("%Y%j %H0000", time.gmtime(secs + hr * 60 * 60))
            a_date,ghr = map(int, gdh.split())
            tflag[hr,:,0] = tflag[hr,:,0] * a_date
            tflag[hr,:,1] = tflag[hr,:,1] * ghr
        rootgrp.variables['TFLAG'][:] = tflag

        # Is it daylight savings time in California?
        if gmt_shift == '19':
            # shift all hours by one
            for hr in xrange(24):
                for grp in grid:
                    grid[grp][:,hr,:,:] = grid[grp][:,hr + 1,:,:]
            # default boundary condition: set 25th hour = first hour
            for grp in grid:
                grid[grp][:,24,:,:] = grid[grp][:,0,:,:]

        # writing all species but time
        for grp in self.groups:
            pos = 0
            while pos < self.groups[grp]['species'].size:
                spec = self.groups[grp]['species'][pos]
                rootgrp.variables[str(spec)][:,0,:,:] = grid[grp][pos,:,:,:] * self.STONS_HR_2_G_SEC / self.groups[grp]['weights'][pos]
                pos += 1

        rootgrp.close()
        grid = {}

    def _create_netcdf(self, out_path, date, jdate):
        ''' Creates a blank CMAQ-ready NetCDF file, including all the important
            boilerplate and header information. But does not fill in any emissions data.
        '''
        # define some header variables
        current_date = int(time.strftime("%Y%j"))
        current_time = int(time.strftime("%H%M%S"))

        # create and outline NetCDF file
        rootgrp = Dataset(out_path, 'w', format='NETCDF3_CLASSIC')
        TSTEP = rootgrp.createDimension('TSTEP', None)
        DATE_TIME = rootgrp.createDimension('DATE-TIME', 2)
        LAY = rootgrp.createDimension('LAY', 1)
        VAR = rootgrp.createDimension('VAR', self.num_species)  # number of variables/species
        ROW = rootgrp.createDimension('ROW', self.nrows)        # Domain: number of rows
        COL = rootgrp.createDimension('COL', self.ncols)        # Domain: number of columns

        # define TFLAG Variable
        TFLAG = rootgrp.createVariable('TFLAG', 'i4', ('TSTEP', 'VAR', 'DATE-TIME',), zlib=False)
        TFLAG.units = '<YYYYDDD,HHMMSS>'
        TFLAG.long_name = 'TFLAG'
        TFLAG.var_desc = 'Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS'

        # define variables and attribute definitions
        varl = ''
        for group in self.groups:
            for species in self.groups[group]['species']:
                rootgrp.createVariable(species, 'f4', ('TSTEP', 'LAY', 'ROW', 'COL'), zlib=False)
                rootgrp.variables[species].long_name = species
                rootgrp.variables[species].units = self.groups[group]['units']
                rootgrp.variables[species].var_desc = 'emissions'
                varl += species.ljust(16)

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
        rootgrp.setncattr('VAR-LIST', varl)     # use this command b/c of python not liking hyphen '-'

        return rootgrp

    def _fill_grid(self, scaled_emissions, date):
        ''' Fill the entire modeling domain with a 3D grid for each pollutant.
            Fill the emissions values in each grid cell, for each polluant.
            Create a separate grid set for each date.
        '''
        species = {}  # for pre-speciated emissions
        grid = {}
        for group in self.groups:
            num_specs = len(np.atleast_1d(self.groups[group]['species']))
            grid[group] = np.zeros((num_specs, 25, self.nrows, self.ncols), dtype=np.float32)
            for i in xrange(num_specs):
                species[self.groups[group]['species'][i]] = {'group': group, 'index': i}

        # loop through the different levels of the scaled emissions dictionary
        for region_data in scaled_emissions.data.itervalues():
            day_data = region_data.get(date, {})
            for hr, hr_data in day_data.iteritems():
                for eic, sparce_emis in hr_data.iteritems():
                    # This is only for pre-speciated cases
                    if eic == -999:
                        for (row, col), cell_data in sparce_emis.iteritems():
                            for poll, value in cell_data.iteritems():
                                grp = species[poll]['group']
                                ind = species[poll]['index']
                                grid[grp][ind,hr,row,col] += value
                        continue
                    # This is for the usual un-speciated case
                    for (row, col), cell_data in sparce_emis.iteritems():
                        for poll, value in cell_data.iteritems():
                            if poll == 'tog':
                                grid['TOG'][:,hr,row,col] += value * self.gspro[self.gsref[int(eic)]['TOG']]['TOG']
                            elif poll == 'pm':
                                grid['PM'][:,hr,row,col] += value * self.gspro[self.gsref[int(eic)]['PM']]['PM']
                            elif poll == 'nox':
                                grid['NOX'][:,hr,row,col] += value * self.gspro['DEFNOX']['NOX']
                            elif poll == 'sox':
                                grid['SOX'][:,hr,row,col] += value * self.gspro['SOX']['SOX']
                            else:
                                grid[poll.upper()][0,hr,row,col] += value

        # setup diurnal boundary condition
        for group in grid:
            grid[group][:,24,:,:] = grid[group][:,0,:,:]

        return grid

    def _load_gsref(self):
        ''' load the gsref file
            File Format: eic,profile,group
            0,CO,CO
            0,NH3,NH3
            0,SOx,SOX
            0,DEFNOx,NOX
            0,900,PM
        '''
        self.gsref = {}

        f = open(self.gsref_file, 'r')
        for line in f.xreadlines():
            ln = line.rstrip().split(',')
            if len(ln) != 3:
                continue
            eic = int(ln[0])
            profile = ln[1].upper()
            group = ln[2].upper()
            if eic not in self.gsref:
                self.gsref[eic] = {}
            self.gsref[eic][group] = profile

        f.close()

    def _load_weight_file(self):
        """ load molecular weight file
            File Format:
            NO          30.006      NOX    moles/s
            NO2         46.006      NOX    moles/s
            HONO        47.013      NOX    moles/s
        """
        # read molecular weight text file
        fin = open(self.weight_file,'r')
        lines = fin.read()
        fin.close()

        # read in CSV or Fortran-formatted file
        lines = lines.replace(',', ' ')
        lines = lines.split('\n')

        self.groups = {}
        # loop through file lines and
        for line in lines:
            # parse line
            columns = line.rstrip().split()
            if not columns:
                continue
            species = columns[0].upper()
            weight = float(columns[1])
            group = columns[2].upper()

            # file output dict
            if group not in self.groups:
                units = columns[3]
                self.groups[group] = {'species': [], 'weights': [], 'units': units}
            self.groups[group]['species'].append(species)
            self.groups[group]['weights'].append(weight)

        # convert weight list to numpy.array
        for grp in self.groups:
            self.groups[grp]['species'] = np.array(self.groups[grp]['species'], dtype=np.dtype('a8'))
            self.groups[grp]['weights'] = np.array(self.groups[grp]['weights'], dtype=np.float32)

        # calculate the number of species total
        self.num_species = 0
        for group in self.groups:
            self.num_species += len(self.groups[group]['species'])

    def _load_gspro(self):
        ''' load the gspro file
            File Format:  group, pollutant, species, mole fraction, molecular weight=1, mass fraction
            1,TOG,CH4,3.1168E-03,1,0.0500000
            1,TOG,ALK3,9.4629E-03,1,0.5500000
            1,TOG,ETOH,5.4268E-03,1,0.2500000
        '''
        self.gspro = {}

        f = open(self.gspro_file, 'r')
        for line in f.xreadlines():
            # parse line
            ln = line.rstrip().split(',')
            profile = ln[0].upper()
            group = ln[1].upper()
            if group not in self.groups:
                sys.exit('ERROR: Group ' + group + ' not found in molecular weights file.')
            pollutant = ln[2].upper()
            try:
                poll_index = list(self.groups[group]['species']).index(pollutant)
            except ValueError:
                # we don't care about that pollutant
                pass
            # start filling output dict
            if profile not in self.gspro:
                self.gspro[profile] = {}
            if group not in self.gspro[profile]:
                self.gspro[profile][group] = np.zeros(len(self.groups[group]['species']),
                                                      dtype=np.float32)
            self.gspro[profile][group][poll_index] = float(ln[5])

        f.close()

    def _build_state_file_path(self, date):
        """ Build output file directory and path for a daily, multi-region NetCDF file.
            NOTE: This method uses an extremely detailed file naming convention.
                  For example:
            st_4k.mv.v0938..2012.203107d18..e14..ncf
            [statewide]_[4km grid].[mobile source].[version 938]..[base year 2012].
            [model year 2031][month 7]d[day 18]..[EIC 14 categories]..ncf
        """
        yr, month, day = date.split('-')

        out_dir = os.path.join(self.directory, 'ncf')
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
                    yr + month + 'd' + day + '..e14..ncf'

        return os.path.join(out_dir, file_name)
