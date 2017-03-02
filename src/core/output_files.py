
from collections import defaultdict
from datetime import datetime as dt
import os


class OutputFiles(defaultdict):
    """ A simple collection of output files, created by ESTA, organized by date. """

    def __init__(self):
        defaultdict.__init__(self, list)

    def __getitem__(self, key):
        """ Getter method """
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        """ Setter method """
        if type(key) != str or type(val) != list:
            raise TypeError('The key of the OutputFiles object must be a date string ' +
                            'and value must be a file path.')
        defaultdict.__setitem__(self, key, val)

    def union(self, new_files):
        """ Combine this object with another of the same type """
        if type(new_files) != self.__class__:
            raise TypeError('Only ' + self.__class__.__name__ + ' objects can be unioned together.')

        for date, file_paths in new_files.iteritems():
            for file_path in file_paths:
                defaultdict.__setitem__(self, date, defaultdict.__getitem__(self, date) + [file_path])


def build_arb_file_path(date, grid_file, file_type, directory='output/', base_year=False,
                        version='v0100', inv_type='mv', region='st', cats='e14'):
    """ Build the final output file name and directory for a single day ESTA output file,
        using the extremely detailed ARB file name convention.

        Inputs:
            date: requires a Datetime object
            grid_file: requires a ARB-name CMAQ grid description file, e.g.
                        GRIDCRO2D.California_4km_291x321
            file_type: this is just the file extension, e.g. pmeds, ncf, txt
            directory: local or absolute path to the desired output directory
                       (If this directory doesn't exist, it will be created.)
            base_year: a 4-digit string representing the year of the inventory
            version: short string, helping to identify this simulation (usually starts with "v")
            inv_type: The two-letter ARB source-type identifying string:
                      mv = mobile sources
                      ar = area sources
                      pt = point sources
                      og = ocean-going vehicles
            region: short string identifying the region this file represents:
                      st = California ("state")
                      us = United States (48 states)
                      wus = Western United States
                      sjv = San Juaquin Valley
                      sc = South Coast Air Basin
            cats: Emissions Categories used in modeling:
                      e14 = ARB's EIC-14
                      e3 = ARB's EIC-3
                      scc = US EPA's SCCs

        Output Format example:
            st_4k.mv.v0938..2012.2031200..e14..pmeds
            [statewide]_[4km grid].[mobile source].[version 938]..[base year 2012].
            [model year 2031][Julian Day 200]..[EIC 14 categories]..[PMEDS format]
    """
    # parse date information
    yr = date.year
    month = date.month
    day = date.day
    if not base_year:
        base_year = str(yr)
    julian_day = str(date.timetuple().tm_yday)

    # ensure output directory exists
    out_dir = os.path.join(directory, file_type)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # define the grid size string
    grid_size = '4k'
    grid_name = os.path.basename(grid_file)
    if '12km' in grid_name:
        grid_size = '12k'
    elif '36km' in grid_name:
        grid_size = '36k'
    elif '1km' in grid_name:
        grid_size = '1k'
    elif '250m' in grid_name:
        grid_size = '250m'

    # build final file name
    file_name = ''.join([region, '_', grid_size, '.', inv_type, '.', version, '..', str(base_year),
                         '.', str(yr), julian_day, '..', cats, '..', file_type])

    return os.path.join(out_dir, file_name)
