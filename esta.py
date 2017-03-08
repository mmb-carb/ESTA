#! /usr/bin/env python

import os
import sys
from src.core.custom_parser import CustomParser
from src.core.esta_model_builder import EstaModelBuilder


def main():
    ''' Parse the command line arguments provided,
        and run ESTA if the arguments are valid.
    '''
    config_file_path = ''
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--h', '-help', '--help']:
        usage()
    elif len(sys.argv) == 2:
        config_file_path = sys.argv[1]
    else:
        usage()

    if not os.path.exists(config_file_path):
        sys.exit('\nERROR: Config file not found: %s\n' % config_file_path)

    process_esta(config_file_path)


def process_esta(config_file_path):
    ''' Parse config file, then
        initialize and run ESTA model
    '''
    # config file parsing
    config = CustomParser(config_file_path)

    # build ESTA model chain, based on config file
    builder = EstaModelBuilder(config)
    model = builder.build()

    # run the ESTA Model
    model.run()


def usage():
    ''' In the event that the command line arguments to this script are invalid,
        print a very brief help menu, describing how to run ESTA from the command line.
    '''
    help_text = '''\n\nESTA Model Usage
\nSimply provide the path to a config file:\n
\t python esta.py config/example_onroad_ca_4km_dtim_pmeds.ini
\t./esta.py /path/to/user_defined_config.ini\n
'''
    print(help_text)
    sys.exit()


if __name__ == '__main__':
    main()
