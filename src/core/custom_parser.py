
from ConfigParser import ConfigParser
from re import split
import sys


class CustomParser(ConfigParser):

    def __init__(self, file_path):
        ConfigParser.__init__(self)
        self.data = {}
        self.read(file_path)
        self._config_to_dict()

    def __getitem__(self, section):
        ''' Allow the config options to be accessed as a 2-deep dictionary. '''
        return self.data.get(section, {})

    def _config_to_dict(self):
        ''' Quickly convert config options into a dictionary '''
        self.data = {}
        for section in self.sections():
            self.data[section] = {}
            options = self.options(section)
            for option in options:
                try:
                    self.data[section][option] = self.get(section, option)
                except:
                    print("Exception parsing file for section/option: %s/%s" % (section, option))
                    self.data[section][option] = None

    def eval(self, key, value):
        ''' Evaluate Python code that is written directly into the config file. '''
        try:
            return eval(self.data[key][value])
        except:
            sys.exit('Exception parsing Python code for section/option: %s/%s' % (key, value))

    def eval_file(self, key, value):
        ''' Read in a Python file and return the evaluated contents. '''
        try:
            return eval(open(self.data[key][value], 'r').read())
        except:
            sys.exit('Exception parsing Python file for section/option: %s/%s' % (key, value))

    def getlist(self, section, option, typ=str, sep=r'\s+'):
        ''' Read in a config value as a list.
            The type of the items in the list can be set with the third parameter.
            By default, this is a white-space separated list. But it the fourth
            parameter to this method can be any character or string.
        '''
        try:
            return [typ(s) for s in split(sep, self.data[section][option].rstrip())]
        except:
            sys.exit('Exception parsing list for section/option: %s/%s' % (section, option))

    def parse_regions(self, key, value):
        """ Parse the string we get back from the regions field """
        regions_str = self.data[key][value]
        if '..' in regions_str:
            regions = regions_str.split('..')
            regions = range(int(regions[0]), int(regions[1]) + 1)
        else:
            regions = [int(c) for c in regions_str.split()]

        return regions
